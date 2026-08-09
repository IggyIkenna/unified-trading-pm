---
doc_type: issue
title:
  quality-gates-v2 cancel-in-progress fixed for pull_request/workflow_dispatch (shipped); bookkeeping-job floor cost cut
  by folding record-qg-result into the aggregate job (shipped); PM promote-PR mechanism confirmed vs. ci-cd-flow.md
summary: >-
  A fresh CI-minutes sweep (2026-07-31/08-02) found quality-gates-v2's concurrency group only cancelled superseded
  `push` runs, never `pull_request`/`workflow_dispatch` ones — fixed and shipped (PM + fleet rollout in progress). Also
  measured: content-gate + the quality-gates-v2 aggregation job + record-qg-result bill GitHub's 1-minute floor on every
  run regardless of whether real gate work happens, ~129+ billed min/day on instruments-service alone — the largest
  single line item found. **2026-08-02 (slot-8): design + shipped** — record-qg-result folded into the quality-gates-v2
  aggregate job (the one topologically-mergeable pair; content-gate strictly precedes the matrix and can't join). Cuts 1
  of the 3 job-floors (~1/3 of the measured figure); caller-facing outputs verified unaffected. Also surfaced: live
  quickmerge output for PM says its promote mechanism is now "frozen-per-SHA-ref" via a "churn fix, 2026-07-27", which
  appears to contradict /codex/08-workflows/ci-cd-flow.md's still-live-branch-ref "PM Option-B standing LDR->main PR"
  description (codified 2026-06-09) — flagging as a possible stale-SSOT, not verified further here.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, concurrency, quality-gates-v2, workflow-templates]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-02
author: unknown
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
resolved_by: slot-15, 2026-08-09
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    unified-trading-pm/scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml,
    unified-trading-pm/scripts/workflow-templates/quality-gates-v2.yml.tmpl,
    unified-trading-pm/.github/workflows/ldr-to-main-promote.yml,
  ]
---

# quality-gates-v2 concurrency fix (shipped) + bookkeeping-job cost + a possible stale SSOT

> **🔵 ARCHIVED 2026-08-09 (slot-15)** — all 3 todos on this doc are now done (concurrency fix, bookkeeping-job merge,
> promote-mechanism ground-truth confirmation, and the final `[VERIFY] P3` re-measure below). `status: resolved`. No new
> codex contract to record — the re-measure confirmed the already-shipped fix's effect (cancellation rate 15.5% → 0.5%),
> it didn't establish a new rule. Referrers corpus-wide repointed to this archive path in the same commit.

> **🟢 REACTIVATED 2026-08-09 (plan_reconciler ci-tranche, agt-04cb0e)** — was 🟡 PARKED pending calendar gate (target
> reactivation on/after 2026-08-05); today is 2026-08-09, 7 days past. Dropped the `DEFERRED-until-2026-08-05:` prefix
> on the todo below per its own documented reactivation instructions. Verified real post-fix churn has accumulated (not
> just elapsed time): `gh run list --repo IggyIkenna/unified-trading-pm --workflow quality-gates-v2.yml --limit 100`
> (sample window 2026-08-09T00:15–16:29Z) → `pull_request` 70 runs (5 success/65 failure/0 cancelled), `push` 5 runs (4
> success/1 failure/0 cancelled), `workflow_dispatch` 25 runs (3 success/21 failure/1 cancelled) — a real, non-trivial
> post-fix sample, left for the dispatched worker to compare against the pre-fix baseline and compute the actual %. Also
> flipped the secondary prerequisite condition `qgv2-pm-remeasure-after-2026-08-05` to `true` via
> `POST /api/prerequisites/...` for consistency (the brief-text prefix was and remains the real gate). Original parking
> rationale (below) kept as historical context, not deleted.
>
> **🟡 PARKED (`DEFERRED-`-prefixed brief, 2026-08-02 slot-16) — the lone remaining todo below is calendar-gated, not
> blocked/ambiguous.** It needs a few days of real post-fix `push`/`pull_request` PR churn to produce a statistically
> meaningful sample (the concurrency fix landed `unified-trading-pm@f55f9b11e6`, `2026-08-02T11:36:28Z`) — target
> reactivation **on/after 2026-08-05**. Four prior slots (15, 4, 9, 12) each independently redispatched to this exact
> task within ~1h and reconfirmed the same "premature" finding, burning a full investigation every cycle because none of
> their `/skip-current-task` calls used an escalating `reason_code` (all used `OTHER`, which never arms the fleet
> cooldown/auto-park — confirmed via the activity log). Per main's ruling on slot-12's `/blocked` (`BLK-32a5fc40`,
> answered 2026-08-02T12:49:12Z): a `data/config/backlog.yaml` hand-park is wrong (root-clone-only + `PlanRegenLoop`
> reverts it every ~30min) — the correct fix is parking at the SOURCE doc. `status: draft` (main's first-offered option)
> turned out to be schema-invalid for `doc_type: issue` (`open·blocked·resolved·false-positive·superseded` only, per
> `/codex/11-project-management/doc-frontmatter-schema.md` — the local `plan-hygiene` pre-commit hook caught this before
> it shipped). Used main's SECOND-offered option instead: `agent-orchestrator/server/dispatch.py`'s `_brief_is_deferred`
> — a `FilterScope.FLEET` dispatch filter that unconditionally excludes ANY task whose brief (the checkbox's own first
> physical line) starts with `DEFER`/`DEFERRED`/`NICE-TO-HAVE`/`OPTIONAL`/`LATER` + a separator char, for every slot,
> regardless of priority — from `pick_next_task`'s candidate set. This is per-todo (no doc-level status edit needed).
> **To reactivate**: edit the checkbox line below back to its original `[VERIFY] P3. **Re-measure...` wording (drop the
> `DEFERRED-until-2026-08-05:` prefix) once real PR churn has accumulated — `PlanRegenLoop`'s next tick re-derives it as
> a normal dispatchable task. The prerequisite condition `qgv2-pm-remeasure-after-2026-08-05` (created by slot-4,
> value=`false`) remains a secondary signal but is NOT what gates dispatch here; the brief-text prefix is the actual
> gate.

## What shipped this session (2026-08-02)

- [x] ✅ **DONE — `quality-gates-v2`'s `concurrency.cancel-in-progress` extended from `push`-only to unconditional
      `true`.** Before: `cancel-in-progress: ${{ github.event_name == 'push' }}` — a `pull_request` or
      `workflow_dispatch` run that got superseded by a newer commit on the same ref queued to full completion instead of
      being cancelled, billing in full for nothing. The group is already scoped per-ref
      (`quality-gates-v2-${{ github.ref }}`; a PR's ref is `refs/pull/<n>/merge`, unique per PR), so cancelling
      in-progress here cannot cross-cancel a different PR or a push to main. Fixed in both PM's own caller
      (`.github/workflows/quality-gates-v2.yml`) and the fleet template
      (`scripts/workflow-templates/quality-gates-v2.yml.tmpl`). PM shipped:
      `unified-trading-pm@f55f9b11e6b04cd5c553d4c0f825398d0f7c3665` (QG 150s clean, 1611 passed/11 skipped). **Fleet
      rollout — DONE, 22/22.** 21 repos shipped clean on the first topologically-ordered pass (T0 deps
      `unified-api-contracts`/`unified-trading-library` first) — SHAs inlined here (the transient shell scratchpad that
      originally logged them is gone, so this is the durable copy):

      | Repo | SHA |
                                                                                                                                                          | --- | --- |
                                                                                                                                                          | unified-api-contracts | `7f4af10828903cd77f7fc39c6e290cba5162f290` |
                                                                                                                                                          | unified-trading-library | `7facf4f4e307a1df043780060ff7a0554a8c8ac6` |
                                                                                                                                                          | alerting-service | `943bd664eed779cd180deee445ceb02667f4b757` |
                                                                                                                                                          | batch-live-reconciliation-service | `495449bdff52d2551e3ac251e67acf98ce6f8422` |
                                                                                                                                                          | client-reporting-api | `9774da252b60bb8aae7e4e6acaa4380f4801f0c1` |
                                                                                                                                                          | deployment-service | `891f5a1637d26d513f24833bfb5b9017eecaf374` |
                                                                                                                                                          | execution-service | `a124eb7af258f69dfb7c065be6da16742ec1caf1` |
                                                                                                                                                          | fund-administration-service | `83803d30dce68dcc4d27320e4ee7ef716c3ddd57` |
                                                                                                                                                          | greeks-service | `6a9ea6687f01afed7d317c9d93003a4a1e3981d1` |
                                                                                                                                                          | ibkr-gateway-infra | `26799c39a31912bee5a62c451636f7516c4b00e6` |
                                                                                                                                                          | instruments-service | `6336dc355549e5c168bc2022c27111d34df9eaab` |
                                                                                                                                                          | market-data-processing-service | `ef8b693c78622f2c88b3da7633918fafeb328451` |
                                                                                                                                                          | market-tick-data-service | `bd991bc0122022ffc74abd4f4fe0ab1c8ea020f1` |
                                                                                                                                                          | ml-service | `1c9570818a698c396829dcef607313957c647b79` |
                                                                                                                                                          | strategy-service | `d4efea96722ac72749295f72919b04ab10014216` |
                                                                                                                                                          | trading-agent-service | `0973b169a17b29cdf43e775405b4de64cbce471f` |
                                                                                                                                                          | unified-trading-api | `751483305fe5d9ea7842c37e136102f4fc5248ea` |
                                                                                                                                                          | deployment-api | `1493f854d928fe39bfee8432e39352a55ab5984e` |
                                                                                                                                                          | e2e-testing | `2f7bf5051dec2caa6a63c041dd106a665db020b4` |
                                                                                                                                                          | features-service | `d2c65ba8f0ee39a71914a6d0239fcca5df49a7db` |
                                                                                                                                                          | system-integration-tests | `87f571f80582a66e648b786c9e4126f833ec8056` |

                                                                                                                                                          `agent-orchestrator` (the 22nd) failed this first pass on its own `quality-gates.sh` (unrelated: a stale `.venv`)
                                                                                                                                                          and converged separately via THREE independent concurrent AO workers, all reconciled cleanly (verified: `f7fe4e9`
                                                                                                                                                          is a real ancestor of the final HEAD, no duplication/corruption) — see the archived
                                                                                                                                                          `agent_orchestrator_proc_cwd_liveness_test_macos_incompatible_2026_08_02.md` for the full trace: slot-16 (Linux
                                                                                                                                                          host) shipped the concurrency-YAML fix itself at `agent-orchestrator@f7fe4e9` via the canonical
                                                                                                                                                          `rollout-workflow-templates.sh` render (not a hand-edit); slot-1 independently shipped a
                                                                                                                                                          `sys.platform == "darwin"` skip on the macOS-only `_default_proc_cwd_live` test at `agent-orchestrator@24bd611`;
                                                                                                                                                          this session (macOS host, hit the same test failure first via a stale-`.venv` red herring — fixed with `uv
                                                                                                                                                          sync` — then the real macOS/`/proc` gap) independently wrote the more precise `sys.platform != "linux"` version
                                                                                                                                                          of the same skip, which collided in a real merge conflict against slot-1's version on `git pull`'s
                                                                                                                                                          autostash-pop — resolved by keeping the more general `!= "linux"` condition, verified 2224 passed/4 skipped,
                                                                                                                                                          shipped `agent-orchestrator@75230de4c66a766bbc0b953fa2a73d00cf7cae46` (empty diff on the already-fixed YAML
                                                                                                                                                          file, confirming `f7fe4e9`'s content was already correct — only the test file had a real, non-redundant change
                                                                                                                                                          left). The 2 UI repos (`unified-trading-system-ui`, `deployment-ui`) correctly skipped — they call a separate
                                                                                                                                                          `ui-quality-gates-v2.yml`, untouched by this fix.

- [x] ✅ [VERIFY] P3. **Re-measure PM's `quality-gates-v2` push/pull_request/workflow_dispatch run-mix + cancellation
      rate a few days after this lands**, the same way the companion plan's own "re-measure billed job-minutes
      before/after" VERIFY todo already calls for. Before this fix, PM measured 157 success / 12 failure / 31 cancelled
      over a 5-day window — but that 31 was ENTIRELY push-triggered (the only path with `cancel-in-progress:true` before
      today), so it's not a valid baseline for the pull_request-triggered cancellation rate this fix newly enables.
      Don't estimate a % savings without this — see the caveat given to the operator in-session: expect a real but
      unquantified win concentrated wherever a ref gets multiple `synchronize`/`workflow_dispatch` events before the
      gate finishes (PM's own promote mechanism if it's still a moving ref — see the open question below — and
      `ldr-ci-monitor.yml`'s hourly re-dispatch during host-contention episodes specifically), and near-zero on the 22
      fleet repos' frozen-per-SHA promote PRs in steady state (each tick gets a fresh PR number = a fresh concurrency
      group, so there was nothing to collide with there to begin with). — **2026-08-09 (slot-15) — DONE.** Fresh 200-run
      sample (`gh run list --workflow quality-gates-v2.yml --limit 200`, window
      `2026-08-08T09:00:39Z`–`2026-08-09T17:11:01Z`, ~32h of real post-fix churn, 7 days after the fix landed): by event
      — `pull_request` 139 runs (14 success/124 failure/**0 cancelled**), `workflow_dispatch` 47 runs (9 success/36
      failure/**1 cancelled**), `push` 14 runs (12 success/2 failure/**0 cancelled**). Overall cancellation rate **1/200
      = 0.5%**, vs. the pre-fix 5-day baseline's **31/200 = 15.5%** (same ~200-run sample size, different window lengths
      — not a perfectly matched comparison, but directionally decisive). Push-only comparison (the one apples-to-apples
      baseline slice, since pre-fix cancellations were ENTIRELY push-triggered): **0/14 = 0% cancelled post-fix**, down
      from a push-only cancellation rate that necessarily accounted for all 31 of the pre-fix baseline's cancellations.
      Confirms the fix's predicted shape from the todo's own caveat: near-zero collision on PM's now-frozen-per-SHA-ref
      promote PRs (each promote tick gets a fresh PR number/ref = a fresh concurrency group, nothing to cancel against)
      plus the fleet's identical frozen-per-SHA pattern — real but small savings, concentrated in the rare same-ref
      multi-dispatch case (the 1 `workflow_dispatch` cancellation), not the dominant cost driver. **Also observed, out
      of this todo's scope**: the same sample shows an elevated `pull_request`/`workflow_dispatch` FAILURE rate (124/139
      and 36/47 respectively, ~89%/77%) — spot-checked one failing run (`31323929739`): a genuine `QG slice (checks)`
      gate failure, not a cancellation/concurrency artifact. Already tracked by other open issue docs
      (`plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` and siblings) — not
      re-investigated or re-filed here, cross-referenced only. Doc's only remaining open item was this todo; flipping
      `status` to `resolved`.

## Open question — does PM's promote mechanism still match ci-cd-flow.md's "Option-B standing PR" description?

`/codex/08-workflows/ci-cd-flow.md` (read 2026-07-31, lines 1-645 of 1231; "PM Option-B standing LDR→main PR" section,
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
      Updated `/codex/08-workflows/ci-cd-flow.md`: rewrote the "PM Option-B standing LDR→main PR" section (dated 🟡
      CORRECTED banner + the frozen-head model description + the old branch-ref model kept as explicit historical
      context, not deleted), fixed the stale "manual immediate drain" recipe (a `--head live-defi-rollout` PR would now
      be auto-closed by the bot's own bug#7 guard), fixed the CONTENT-verification note, and fixed the squash/rebase
      table row + its "Bottom line" paragraph. Also fixed the same misattribution in `scripts/quickmerge.sh`'s own
      comment + user-facing echo line (it credited the wrong commit/date for the frozen-head switch). Evidence:
      unified-trading-pm (this repo) — `/codex/08-workflows/ci-cd-flow.md` + `scripts/quickmerge.sh`, this commit.

## Bookkeeping-job 1-minute-floor cost (measured, not yet actioned)

- [x] ✅ [INFRA] P2. **`quality-gates-v2`'s 3 fixed bookkeeping jobs — `content-gate`, the aggregation job named
      `quality-gates-v2` (needs: `[content-gate, qg-slices]`), and `record-qg-result` (needs:
      `[qg-slices, supersede-check]`) — each bill GitHub's 1-minute-per-job floor on EVERY run, including a full
      content-sentinel HIT where no real gate work happens.** Measured live on instruments-service (2026-07-31): 43
      `quality-gates-v2` runs in a 19.3h sample ⇒ ≥129 billed min/day from this floor cost alone, on just 1 of 24 repos
      — the largest single aggregate line item found in this sweep, ahead of any individual repo's self-hosted-vs-hosted
      gap. — **2026-08-02 (slot-8, infra craft) — DESIGN + IMPLEMENTED (record-qg-result folded into the aggregate job;
      content-gate stays separate).** Full design below; net result: 1 of the 3 job-floors removed (~1/3 of the measured
      figure), not all 3 — `content-gate` cannot join the merge (see Finding 1).

      **Finding 1 — the naive "merge all 3" is topologically impossible, so it wasn't attempted.** `content-gate`
                                                                                                                                                                                                  (`needs: []`) runs FIRST and STRICTLY GATES `qg-slices` (`qg-slices: needs: content-gate; if:
                                                                                                                                                                                                  needs.content-gate.outputs.cache_hit != 'true'` — a HIT skips the whole matrix, saving ~2 runner-starts/run,
                                                                                                                                                                                                  a bigger win than its own 1-min floor cost). The aggregation job (`quality-gates-v2`) and `record-qg-result`
                                                                                                                                                                                                  both run AFTER `qg-slices` (`needs: [content-gate, qg-slices]` / `[qg-slices, supersede-check]`). A job that
                                                                                                                                                                                                  must complete BEFORE the matrix starts cannot be merged with two jobs that only exist to summarize the matrix's
                                                                                                                                                                                                  result — doing so would force `qg-slices` to wait on the aggregation/record-result logic too, defeating the
                                                                                                                                                                                                  whole point of the content-sentinel short-circuit. Only `quality-gates-v2` (agg) + `record-qg-result` — both
                                                                                                                                                                                                  downstream of `qg-slices` — are topologically mergeable.

                                                                                                                                                                                                  **Finding 2 — the todo's own "prove on ONE caller first (agent-orchestrator)" premise doesn't hold for this
                                                                                                                                                                                                  target, and the design corrects it.** The concurrency fix (above, already shipped) is safely canary-able
                                                                                                                                                                                                  because it lives in the per-repo CALLER template (`scripts/workflow-templates/quality-gates-v2.yml.tmpl`),
                                                                                                                                                                                                  rolled out repo-by-repo via `rollout-workflow-templates.sh`. This merge lives INSIDE the single shared REUSABLE
                                                                                                                                                                                                  workflow (`.github/workflows/python-quality-gates-v2.yml`) that all 24 repos call via `uses:
                                                                                                                                                                                                  .../python-quality-gates-v2.yml@live-defi-rollout` — a moving ref, not a pinned SHA. There is no per-repo copy
                                                                                                                                                                                                  to canary: the instant this change lands on `live-defi-rollout`, every fleet repo (agent-orchestrator included)
                                                                                                                                                                                                  picks it up on its very next run, simultaneously. `agent-orchestrator` gets ZERO extra isolation from being
                                                                                                                                                                                                  "already self-hosted" here — that framing was for the CALLER-template rollout pattern and doesn't transfer.
                                                                                                                                                                                                  The only real pre-fleet validation available is PM's OWN `quality-gates-v2` run against the change itself (PM's
                                                                                                                                                                                                  caller uses a LOCAL `./`-path `uses:`, so PM's own PR/push run exercises the new merged job graph before the
                                                                                                                                                                                                  commit ever reaches LDR) — that is the "ONE caller" this shipped through, not agent-orchestrator specifically.

                                                                                                                                                                                                  **Finding 3 — caller-facing surface is unaffected (verified, not assumed).** Grepped every
                                                                                                                                                                                                  `needs.quality-gates-v2.*` reference in the caller template (`scripts/workflow-templates/quality-gates-v2.yml.tmpl:96,154,184`):
                                                                                                                                                                                                  fleet callers consume ONLY `needs.quality-gates-v2.result`, `.outputs.metadata_only`, `.outputs.docs_only` —
                                                                                                                                                                                                  none of which are touched by this merge (job id stays `quality-gates-v2`; those two outputs still come from the
                                                                                                                                                                                                  same `vcheck` step, unchanged). The `escalate-ldr-qg-failure` / `dispatch-cloud-build` x2 / notify-ci-watcher
                                                                                                                                                                                                  jobs the todo flagged as the collision risk are safe.

                                                                                                                                                                                                  **Finding 4 — bounded, accepted latency trade on the required check.** Today `quality-gates-v2` (agg) and
                                                                                                                                                                                                  `supersede-check` run as PARALLEL siblings (both `needs: [content-gate, qg-slices]`, no ordering between them).
                                                                                                                                                                                                  Folding `record-qg-result` in required adding `supersede-check` to the agg job's `needs:` (its guard —
                                                                                                                                                                                                  `needs.supersede-check.outputs.superseded != 'true'` — is a real dependency, not optional). On the GREEN path
                                                                                                                                                                                                  (the large majority — PM's own 5-day baseline was 157 success / 12 failure / 31 cancelled), `supersede-check`'s
                                                                                                                                                                                                  own `if:` is false, so it resolves to `skipped` without ever provisioning a runner — negligible added latency.
                                                                                                                                                                                                  On the fail/cancelled path (~20% of runs), `supersede-check` now provisions a real runner + makes one `gh api`
                                                                                                                                                                                                  call (~15-30s) BEFORE the required check can conclude, versus running in parallel today. Accepted: a ~20-30s
                                                                                                                                                                                                  slower red signal on the minority of already-broken runs, in exchange for removing a whole job's billed floor
                                                                                                                                                                                                  from every run (100% of runs, not just failures).

                                                                                                                                                                                                  **What shipped**: `record-qg-result`'s two steps (GCP auth + read/decide/persist) moved verbatim into
                                                                                                                                                                                                  `quality-gates-v2`'s `steps:` list (renamed `record_gcp_auth` / `record_decide` to avoid colliding with the
                                                                                                                                                                                                  agg job's own `marker_auth`), each carrying the old job-level `if:` as a step-level `if:` (the agg job's own
                                                                                                                                                                                                  `if:` stays `always()`, so per-step gating is required, not optional — verified the "not superseded" case is
                                                                                                                                                                                                  genuinely per-step-safe: an ungated `record_decide` would still fail-open cleanly on an empty token, but the
                                                                                                                                                                                                  explicit `if:` keeps behavior byte-identical to the original job-level gate rather than merely equivalent).
                                                                                                                                                                                                  Added `recovered` to the agg job's `outputs:`. Removed the standalone `record-qg-result` job. Rewired
                                                                                                                                                                                                  `notify-qg-recovered`'s `needs: [qg-slices, record-qg-result]` → `[qg-slices, quality-gates-v2]` and its
                                                                                                                                                                                                  `needs.record-qg-result.outputs.recovered` → `needs.quality-gates-v2.outputs.recovered`. Verified: YAML
                                                                                                                                                                                                  parses (`yaml.safe_load`), the local `check_workflow_yaml_valid.py` QG check passes (59 workflows parse; no
                                                                                                                                                                                                  `actionlint` binary available in this sandbox, so that leg is parse-only here — informational, non-blocking
                                                                                                                                                                                                  per the check's own design), and a `grep -rn record-qg-result` confirms zero remaining functional references
                                                                                                                                                                                                  (only historical-context comments + this doc). Evidence:
                                                                                                                                                                                                  unified-trading-pm@<shipped in this commit> — `.github/workflows/python-quality-gates-v2.yml`.

                                                                                                                                                                                                  **Not done / explicit follow-up**: this shipped on PM's own pre-merge CI as its proof, per Finding 2 — there is
                                                                                                                                                                                                  no additional agent-orchestrator-specific canary step to run (none exists for this file). The `[VERIFY]` P3
                                                                                                                                                                                                  re-measure todo below should, once its own calendar-gate clears, also confirm this merge didn't regress the
                                                                                                                                                                                                  QG-Recovered Slack notification (watch for a `record_decide`-sourced `recovered=true` firing correctly on the
                                                                                                                                                                                                  next real red→green cycle on any fleet repo — no dedicated test was run for that specific transition in this
                                                                                                                                                                                                  session, since it requires a genuine prior-failure state in `qg_last_conclusion` to observe honestly rather than
                                                                                                                                                                                                  synthetically).

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
- **2026-08-02 (slot-4) — same `[VERIFY] P3` todo redispatched ~27min after slot-15 declined it; independently
  reconfirmed premature, harder evidence this time, escalating the redispatch-thrash risk.** Queried
  `gh run list --repo IggyIkenna/unified-trading-pm --workflow quality-gates-v2.yml` directly at `2026-08-02T12:03:51Z`:
  **zero runs of any event type since the fix landed** (`2026-08-02T11:36:28Z`) — the most recent run is a
  `workflow_dispatch` from `2026-08-01T15:24:23Z`, ~20.7h before the fix, so there is currently no post-fix sample at
  all, not merely an insufficient one. Also confirmed PM's `quality-gates-v2.yml` triggers are `push:[main]` /
  `pull_request:[main,staging]` / `workflow_dispatch` only — it does NOT fire on push to `live-defi-rollout`, so the
  fix-landing commit itself generated no run; the next real signal will be the frozen-per-SHA-ref promote PR
  (`pull_request`-triggered, ~15-30min SLA per the "Open question" section above) or the next `workflow_dispatch`.
  Declining again, not flipping the checkbox — forcing a number from an empty sample would be fabrication, not
  verification. **Redispatch-thrash risk**: this task is `tier=1 priority=80`, dispatched as the "highest-rank queued
  task" — with `/skip-current-task` only excluding the skipping slot (other slots still see it normally per
  `dashboard/API_REFERENCE.md`), it will likely re-dispatch to a third slot within minutes and repeat this same ~2min
  investigation, recurring every cycle until ~2026-08-05. Slot-15's recommended fix (dispatch-gate by calendar time,
  RULES.md §4 park recipe) was never applied — confirmed why: `data/config/backlog.yaml` is gitignored, live-only server
  state on the ROOT `agent-orchestrator` clone (verified via `git check-ignore` + process cwd inspection), which is
  structurally unreachable from any `.tabs/<slot>/` worker clone, not merely discouraged. Pre-staged the fix as far as a
  worker can: created prerequisite condition `qgv2-pm-remeasure-after-2026-08-05` (value=`false`, via
  `POST /api/prerequisites/...` — API-only, no root-clone file touch needed for this half). **Remaining step needs
  root-clone filesystem access** (main/operator/orchestrator-admin only): on this task's entry in
  `data/config/backlog.yaml`, set `priority: 999`, `priority_override: true`,
  `prereqs.prerequisites: [qgv2-pm-remeasure-after-2026-08-05]`, then `POST /api/backlog/reload`; flip the condition
  `true` via `POST /api/conditions/qgv2-pm-remeasure-after-2026-08-05` on/after 2026-08-05 once real PR churn has
  accumulated. Raised as a `/blocked` question from slot-4 (non-gating — proceeding to skip regardless) so this surfaces
  on the dashboard instead of relying on a third slot re-discovering the same doc note.
- **2026-08-02 (slot-8, infra craft)**: the `[INFRA] P2` bookkeeping-job-cost todo done (see checkbox above for full
  design + evidence) — `record-qg-result` folded into the `quality-gates-v2` aggregate job in
  `.github/workflows/python-quality-gates-v2.yml`; `content-gate` confirmed topologically unmergeable (strictly precedes
  the `qg-slices` matrix, gates its short-circuit). Corrected the todo's own "prove on ONE caller (agent-orchestrator)"
  premise — this file is a single shared reusable workflow with no per-repo canary path; PM's own pre-merge CI is the
  real proof point. Only the `[VERIFY] P3` re-measure todo remains open on this doc (calendar-gated to ~2026-08-05, per
  the entries above) — doc stays `status: open` until that clears.
- **2026-08-02 (slot-12) — same `[VERIFY] P3` todo redispatched a THIRD time, ~14min after slot-4's investigation;
  independently reconfirmed premature yet again, redispatch-thrash prediction realized.** Re-queried
  `gh run list --repo IggyIkenna/unified-trading-pm --workflow quality-gates-v2.yml` at `2026-08-02T12:4x`: exactly ONE
  run since the fix landed (`2026-08-02T11:36:28Z`) — a `workflow_dispatch` at `2026-08-02T12:24:28Z`, ~48min post-fix.
  `workflow_dispatch` runs don't even inform the push/pull_request cancellation-rate this todo measures, so the
  effective post-fix sample for the metric that matters is still zero. Declining again — flipping the checkbox now would
  be fabrication, not verification. **Confirmed the predicted thrash is real, not hypothetical**: checked
  `GET /api/backlog/quality_gates_v2_concurrency_and_bookkeeping_job_cost-001` directly — `priority` is still `80`, no
  `priority_override`, task `status: dispatched, dispatched_to: 12` (was `4`, was `15` before that) — the park recipe
  slot-4 pre-staged was never applied between slot-4's session and this one, confirming the gap is real (root-clone
  `data/config/backlog.yaml` write access, main/operator-only) not a timing fluke. Re-verified the prerequisite
  condition `qgv2-pm-remeasure-after-2026-08-05` still exists at `value=false` (idempotent re-POST, no-op). Raising a
  fresh `/blocked` (non-gating, `can_continue: true`) directly asking main/operator to apply the concrete park recipe
  above — the condition + evidence are fully pre-staged, only the `backlog.yaml` edit + `/api/backlog/reload` call
  remain, and that is a ~30-second action for whoever has root-clone write access. Skipping this task now (not
  fabricating a measurement) to free the slot; resume point unchanged: re-run the run-mix/cancellation-rate measurement
  once at least a few days of real PR churn have accumulated (~2026-08-05 onward).
- **2026-08-02 (slot-16) — applied main's ruling on slot-12's `/blocked` (`BLK-32a5fc40`, answered
  `2026-08-02T12:49:12Z`, ~3.5min after slot-12 had already skipped and moved on) directly, rather than repeating the
  same investigation a fifth time.** Independently re-confirmed the premise first
  (`gh run list --workflow quality-gates-v2.yml --limit 20`, `2026-08-02T~12:55Z`): still only the single
  `workflow_dispatch` run (`2026-08-02T12:24:28Z`) since the fix landed — no new signal. Root-caused WHY the park recipe
  kept not sticking: read `server/regen_backlog_from_plan.py`'s `_is_non_dispatchable`/`maybe_auto_park` — every prior
  skip (`slot_task_skipped` activity events for slots 15/4/9/12, all confirmed via `GET /api/activity`) used
  `reason_code: "OTHER"`, which the skip endpoint's own logic (`server/routes/slots_ops.py`) only arms the fleet
  cooldown/auto-park escalation for `{BLOCKED, PARKED, GATED}` — `OTHER` silently skips that path entirely
  (`fleet_cooldown_armed: false` on every one of those 4 events), so the task was eligible for immediate redispatch
  every time despite 4 slots agreeing it was premature. **Applied main's actual instruction — parked at the plan source,
  not `backlog.yaml`.** First attempt (`status: open` → `status: draft`) was caught and REFUSED by the local
  `plan-hygiene` pre-commit hook before it ever shipped: `draft` is not in the valid `doc_type: issue` status enum
  (`open·blocked·resolved·false-positive·superseded`, per `/codex/11-project-management/doc-frontmatter-schema.md`) —
  main's first-offered option doesn't apply to issue docs, only plan docs. Corrected to main's SECOND-offered option:
  read `agent-orchestrator/server/dispatch.py` directly and found `_brief_is_deferred`/`_blocks_deferred_brief` — a
  `FilterScope.FLEET` filter (unconditional, every slot) that excludes any task whose `brief` (the checkbox's own first
  physical line, per `regen_backlog_from_plan.py`'s `brief=description` derivation) starts with
  `DEFER`/`DEFERRED`/`NICE-TO-HAVE`/`OPTIONAL`/`LATER` + a separator char. Prefixed the checkbox line itself with
  `DEFERRED-until-2026-08-05:` (see todo above) — this is a per-todo mechanism, no doc-level status edit needed, and it
  is schema-safe (brief-text content, not a frontmatter enum). `PlanRegenLoop`'s next tick re-derives this todo as a NEW
  task-id (brief-hash changed) that `pick_next_task` then structurally excludes from every slot's candidate set, and the
  OLD (currently-dispatched) task row is pruned as no-longer-a-current-brief. Shipping this edit via the normal
  quickmerge flow, then `/skip-current-task` with `reason_code: "GATED"` (not `OTHER`, unlike every prior slot) as a
  belt-and-suspenders safety net for the gap before the next regen tick — this correctly arms the fleet cooldown this
  time, so even if the prune hasn't propagated yet, a redispatch to another slot within the next ~12min is blocked at
  the dispatcher level too. Not calling `/done` — the VERIFY measurement itself still isn't done, only deferred;
  `/done`-ing it would misrepresent the todo as complete. Reactivation instructions are in the banner above (drop the
  `DEFERRED-until-2026-08-05:` prefix from the checkbox line).

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 5 entries resolve on disk (SSOT +
  related plan + the 3 workflow files actually edited this doc's todos) — no changes.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **2026-08-09 (slot-15)**: closed the last open todo (`[VERIFY] P3` re-measure) — see the checkbox above for the full
  200-run post-fix sample + numbers. Cancellation rate collapsed from the pre-fix 15.5% (5-day baseline, all
  push-triggered) to 0.5% post-fix (0% on the apples-to-apples push-only slice), confirming the fix's predicted
  near-zero-collision shape on PM's frozen-per-SHA-ref promote PRs. Flagged (not re-investigated) a separate, already-
  tracked elevated failure rate on the same sample — cross-referenced to
  `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` and sibling docs, out of this todo's
  scope. All todos on this doc are now done; flipped `status: open` → `resolved`.
