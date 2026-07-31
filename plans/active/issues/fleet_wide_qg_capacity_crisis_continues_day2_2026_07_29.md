---
doc_type: issue
title:
  Fleet-wide QG self-hosted-runner capacity crisis (fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md) is
  still active into a second day — that doc hit its 1000-line hard cap so this is a continuation, not a duplicate
summary: >-
  Responding to an operator #ci-failures Slack dump (2026-07-28 22:40-2026-07-29 01:29 BST) asking whether the flood of
  QG FAILED/RECOVERED flapping, sit-unlock failures, and stuck promotion PRs indicates an ongoing unresolved problem:
  **yes, confirmed live via the AO escalation API** (`GET /api/escalations/active`, SSM against `i-0c9b283b31d6b5ca7`),
  not assumed from the Slack dump alone. As of 2026-07-29T01:05-01:08Z: 47 `ldr_qg_failure` escalations active in the
  trailing 6h window across ~30 repos, of which 6 terminated `still_red_past_deadline` (genuine give-ups, not fixed —
  including `market-tick-data-service` at 46 attempts and `trading-agent-service` at 78 attempts before eventually going
  green) and several more actively re-escalating (`still_red_reescalated`) in a live retry loop at query time
  (`instruments-service`, `e2e-testing` twice). This is the exact same root cause
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` has tracked since 2026-07-27 — shared 16-vCPU/32GB
  box `i-0c9b283b31d6b5ca7` oversubscribed by ~13-20 concurrent AO slot-worker sessions plus up to 22 self-hosted CI
  runner pools — but that doc is now at its 1000-line hard cap (`wc -l` = exactly 1000) and cannot take a new Progress
  Log entry, hence this continuation doc rather than appending. Separately, and NOT yet diagnosed in the original doc:
  `unified-trading-pm`'s own `plan_health` escalation queue (a DIFFERENT `wall_type`, not `ldr_qg_failure`) is actively
  GROWING, not draining — 44 active `plan_health` entries at query time (was ~34 per the operator's own dashboard
  screenshot earlier the same session), spanning 12 distinct promote-PR incarnations (#1740-#1751) in roughly 5 hours,
  every one `status=dispatched`/`resolved_at=null`. The specific trio the operator asked to be watched (PR
  #1746/#1747/#1748, escalation ids `agt-6a6ba6`/`agt-4c0ede`/`agt-4de402`) had NOT cleared as of this check: all three
  still `status=dispatched`, `resolved_at=null`, 44-51 minutes elapsed since their own dispatch (past the 30-40min
  window originally asked about) — and 4 newer PM promote PRs (#1748-#1751) had already queued up behind them in the
  same window, consistent with a queue that isn't keeping pace with its own inflow rather than one that's merely slow.
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting]; continuation of the
  # fleet_wide_qg_self_hosted_runner_capacity_crisis ci-tranche incident, same content class.
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, incident, cross-repo, escalation-queue, plan-health, github-actions-cost]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /plans/active/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-29
last_updated: 2026-07-31
priority: P1
parent_epic: infrastructure_master
source:
  "operator #ci-failures Slack dump + operator ask to verify PM#1746/1747/1748 + 2 ldr_qg_failure items over 30-40min,
  2026-07-29 ~01:05Z"
execution_scope: local-only
assigned_role: cicd
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Fleet-wide QG capacity crisis continues into day 2 (2026-07-29) — original doc at line cap

## Why this doc exists instead of an entry in the original

`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is at exactly 1000 lines (the hard cap enforced by
`check_line_caps.sh`) — confirmed via `wc -l` before attempting to append. That doc's own root-cause analysis, timeline,
and the operator's 2026-07-28 "protected-6 repos stay self-hosted, accept recurring reds, resolve via retrigger" ruling
all still stand; nothing here supersedes them. This is a same-root-cause continuation entry that had nowhere to land.

## Live verification, 2026-07-29 ~01:05-01:08Z (via AO `GET /api/escalations/active`, SSM)

**`ldr_qg_failure` wall_type, 6h trailing window, 47 entries across ~30 repos:**

- 6 terminated `still_red_past_deadline` (genuine unresolved failures, not fixed): `instruments-service`#1007 (3
  attempts), `agent-orchestrator`#0 (3 attempts), `features-service`#893 (8 attempts), `market-tick-data-service`#774 (2
  attempts), `trading-agent-service`#363 (10 attempts), `market-tick-data-service`#0 (**46 attempts**).
- 1 resolved `qg_v2_green` only after **78 attempts** (`trading-agent-service`#364).
- At query time, several still actively re-escalating (`still_red_reescalated`, i.e. genuinely red again, looped back
  into a fresh dispatch cycle rather than terminally given up): `instruments-service` (×2 rows, one immediately
  re-dispatched), `e2e-testing` (×2 rows).
- Remainder either genuinely `qg_v2_green` (real fixes/self-heals) or still `dispatched` mid-flight.

**This matches `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s signature exactly** — the doc's last
logged entry was 2026-07-28 ~23:26Z (`instruments-service`#1007, `uv` cache race + typecheck timeout + duration miss,
confirmed non-code via clean local QG at the same HEAD); this check ~2h later shows the identical pattern continuing,
unabated, into 2026-07-29.

**`plan_health` wall_type on `unified-trading-pm` specifically — NOT covered by the original doc, distinct symptom:**

44 active entries at query time (`now=2026-07-29T01:05:17Z`), all `status=dispatched`, all `resolved_at=null`, spanning
promote-PR incarnations #1740 through #1751 (12 PRs in ~5h — i.e. a fresh promote PR roughly every 25min, consistent
with `ldr-to-main-promote-fleet.yml`'s `*/15` cadence plus PM being an unusually active repo). The operator-flagged
trio:

| escalation_id | PR   | created (UTC) | dispatched (UTC) | status     | resolved_at | elapsed since dispatch |
| ------------- | ---- | ------------- | ---------------- | ---------- | ----------- | ---------------------- |
| `agt-6a6ba6`  | 1746 | 23:34:02      | 00:17:38         | dispatched | null        | ~51min                 |
| `agt-4c0ede`  | 1747 | 23:41:07      | 00:18:37         | dispatched | null        | ~50min                 |
| `agt-4de402`  | 1748 | 23:51:17      | 00:21:04         | dispatched | null        | ~47min                 |

**Answer to the operator's direct ask: no, this trio had not cleared within 30-40min — nor within the ~50min this check
ran at.** Whether `plan_health` escalations on PM are being starved by the same host-contention root cause (a
`plan_health` worker is presumably itself a slot session competing for the same oversubscribed box) or have a separate,
undiagnosed bottleneck is **not yet determined** — flagging as open rather than assuming either.

## Why this matters for the original CI-cost-reduction thread

This session's original mandate was auditing/reducing GH Actions spend (~$1,150-1,200/mo baseline measured 2026-07-15).
A `trading-agent-service` PR needing **78 retry attempts** before going green, and a `market-tick-data-service`
escalation racking up **46 attempts** before giving up entirely, represent exactly the kind of CI-minute waste that
audit was meant to catch — except this waste is _retry churn from host contention_, not from slow tests or heavy
libraries. The self-hosted-runner migration (this session's own earlier fix, intended to CUT GH-hosted-minute spend) is
the proximate trigger: it moved CI load onto a box that can't sustain it, and the resulting retry storm may be burning
more wall-clock/compute (on infra you're already paying for) than the GH minutes it saved. This is worth quantifying,
not just noting.

## Todos

- [x] ✅ [DATA] P1. Quantify actual cost impact: pull attempt-count distribution across all `ldr_qg_failure` escalations
      over the incident's full 2026-07-27→present window (not just the 6h sample here) and estimate GH-Actions-minute
      waste from cancelled/timed-out/retried runs vs. the self-hosted migration's original projected savings — the
      operator asked for this audit's numbers to be real, not assumed. **DONE 2026-07-30T10:54-11:05Z (slot 5,
      data_engineering) — real numbers pulled from the AO SQLite state.db directly (bypasses the
      `/api/escalations/active` API's hardcoded `.limit(100)` rows, confirmed too small to cover the full window) + real
      GH Actions run history via `gh api`/`gh run list`. See Progress Log entry below for the full breakdown and
      methodology. Verdict: the retry storm's GH-Actions-DOLLAR waste is real but small
      (~$10 over the sampled 3.5-day window, ≈$90/mo if sustained) — roughly 2-3% of the migration's ~$350-450/mo
      projected fleet savings, not big enough to threaten it. The bigger, genuinely unquantified-here cost is AWS EC2
      wall-clock/compute on the oversubscribed shared host from the 815 real agent-dispatch attempts — a different cost
      bucket than what this todo asked about (GH-Actions-minutes), flagged as a new follow-up rather than
      assumed-covered.**
- [x] ✅ [OPERATOR] P1. **Operator-ruled 2026-07-29 (interactive decision session)**: keep protected-6 on self-hosted,
      relying on the just-applied host fix (instance resize + added swap) to cut retry-storm frequency, re-measured
      before any further change. Revisit the 2026-07-28 "protected-6 stay self-hosted, accept recurring reds, resolve
      via retrigger" posture now that it has run into a second day with a 46-attempt and a 78-attempt case — the
      original doc's own Progress Log flagged this exact question ("worth an urgent re-look... rather than treating each
      new instance as just another routine corroboration") before hitting its line cap; it was never answered.

- [x] ✅ [BACKEND] P2. **Re-measure protected-6 retry-attempt counts post-resize** (`i-0c9b283b31d6b5ca7` or successor)
      — the follow-up the 2026-07-29 ruling above is conditioned on. If 46/78-style escalations recur despite the host
      fix (instance resize + added swap), that is the trigger to revisit reverting protected-6 to GitHub-hosted runners;
      if they don't, this posture is confirmed working and this todo can close citing the measurement. **Re-measured
      2026-07-30, ~06:20-06:27Z (this session's operator-ruling close-out pass) — the AO escalations API itself could
      NOT be queried (see Progress Log entry below for the full host-level measurement); host-level evidence answers the
      todo's underlying question directly: the box remains severely oversubscribed post-resize, closing this todo with a
      NEGATIVE verdict (the host fix has NOT resolved the contention) rather than a positive confirmation.**
- [x] ✅ [BACKEND] P2. Diagnose whether PM's `plan_health` escalation queue (44 active, growing, none resolving) shares
      the `ldr_qg_failure` box-contention root cause or has an independent bottleneck — check whether a `plan_health`
      worker type is actually being spawned/claiming slots at all, vs. queuing indefinitely for lack of a matching
      worker (a distinct failure mode from "slow due to contention"). **DIAGNOSED 2026-07-30 (slot 4, backend_engineer)
      — SAME root cause, no independent bottleneck; a genuine but different mechanism than pure host contention. Full
      breakdown in Progress Log below.**
- [x] ✅ [SCRIPT] P2. **DONE — already satisfied, verified 2026-07-31 (slot 11, backend_engineer/cicd).** The split this
      todo asks for already happened, independently of a Recommended-fix-path revisit: the original doc's own
      `## Follow-up` section (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` L307-309) records **"✅
      DONE 2026-07-29 — `## Progress Log` history hoisted to
      `/plans/archive/2026_07/fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_07_29.md` (768
      lines extracted, doc went from 1015L to 250L)"** — triggered by hitting the 1000-line hard cap directly, not by a
      Recommended-fix-path revisit (that section's 4 items were all `[x]`-decided 2026-07-28 and haven't been reopened
      since). Verified today the split is holding up and doing exactly what this todo wanted: original doc currently
      **313 lines** (wc -l, ~700 lines of headroom under the 1000 cap) and its `## Progress Log` has taken **3 fresh
      corroboration entries since the split** (2026-07-29 ~15:51 UTC market-tick-data-service, 2026-07-30 ~15:14 UTC
      features-service, 2026-07-31 ~01:35 UTC features-service) with no need to spin up another sibling doc — i.e.
      corroborations now have somewhere to land, which was this todo's entire goal. (This continuation doc itself is at
      657 lines and growing — worth the same treatment eventually, but that's a fresh observation, not this todo's
      scope; not opening a new todo for it here since nothing is currently blocked.) No code change; no further split
      needed right now.
- [ ] [DATA] P2. **New, opened by the P1 cost-quantification finding above.** The retry storm's real, expensive cost
      bucket is AWS EC2 wall-clock/compute on the oversubscribed shared host (`i-0c9b283b31d6b5ca7`) from the 815 real
      agent-dispatch attempts recorded against `ldr_qg_failure` escalations since 2026-07-27 (self-hosted GH Actions
      runner minutes are free from GitHub's side, so this is NOT GH-Actions-billed — a genuinely separate cost category
      the P1 todo's "GH-Actions-minute" framing didn't cover). Quantify it: pull the box's real AWS Cost Explorer /
      instance-hours data for the 2026-07-27→present window (the box is `m8i.4xlarge`, on-demand or reserved — check
      which) and estimate
      $ cost attributable to the retry-storm's share of CPU/wall-clock vs. steady-state baseline
      usage. Done when: a real $
      figure (not assumed) is added alongside this doc's existing GH-Actions-dollar figure, so the two cost buckets can
      be compared side-by-side.
- [ ] [OPERATOR] P3. Confirm the OOM-killer mechanism for the 2026-07-30 14:54-15:01Z mass `tmux_session_lost` cluster
      (slots 1, 4, 5, 9, 10, 11 killed across 3 waves in ~7 min, see Progress Log below) via `dmesg`/`journalctl -k` on
      `i-0c9b283b31d6b5ca7` (needs root — no agent session has it). Currently UNCONFIRMED: swap (14-16Gi used) + load
      (peak ~26/16vCPU) are consistent with memory pressure but the kernel OOM-killer log has not been read this session
      or any prior one in this doc.
- [ ] [BACKEND] P3. **New, opened by the `plan_health` diagnosis above.** `server/escalation.py`'s
      `retry_queued_escalations()` caps queued-escalation retries at `RETRY_PER_TICK = 2` per `AutoSpawnLoop` tick
      (default 60s), shared GLOBALLY across every `WALL_TYPES` value (not partitioned per wall_type) — a deliberate
      tradeoff (own code comment: "a burst must not starve the task queue forever") that becomes the binding throughput
      ceiling during a genuine multi-wall-type incident burst (91 combined `ldr_qg_failure`+`plan_health` active
      escalations at this doc's 2026-07-29T01:05Z snapshot, all sharing this one 2-per-tick budget). Consider whether
      the cap should scale with queue depth, or partition budget per wall_type, so an `ldr_qg_failure` flood can't
      starve `plan_health`'s (or vice versa) dispatch attempts. Done when: either a deliberate "leave as-is, here's why"
      ruling is recorded, or a scaled/partitioned retry budget ships + is verified to cut tail dispatch latency on the
      next comparable burst.
- [x] ✅ [SCRIPT] P2. **New, opened by the `main-backmerge-to-ldr` pipefail+`-e` root-cause fix below.** The template
      SSOT (`unified-trading-pm@598aefd8`) and 2 repos' live copies (`features-service@ccd01cb8`,
      `agent-orchestrator@d43bbde`) are fixed, but `detect_template_drift.py --workflows` shows this template has 28
      baselined/grandfathered-drift + more not-yet-diverged copies across the ~25-repo fleet — every repo still on the
      OLD copy carries the SAME latent bug (silently dies, zero output, whenever the oldest commit in a
      `live-defi-rollout..main` range lacks a `Promoted-From-LDR:` trailer — not rare, any non-squash-promote commit mix
      triggers it). Run the fleet-wide rollout
      (`bash scripts/workflow-templates/rollout-workflow-templates.sh     --template main-backmerge-to-ldr.yml`, no
      `--repo` filter) + a quickmerge per touched repo, once host capacity allows (this session deliberately scoped to
      only the 2 repos actively observed broken, to avoid piling more QG load onto the same contended box this doc
      tracks). Done when: `detect_template_drift.py --workflows` shows 0 copies still carrying the pre-fix content for
      this template. **DONE 2026-07-31 (slot 4, cicd)** — a dry-run against the actual auto-rollout target set (not the
      todo's assumed ~25) found only 5 repos genuinely still on pre-fix content (`system-integration-tests@2d35879`,
      `trading-agent-service@6de84ab`, `unified-trading-system-ui@4a298786`, `deployment-ui@6f9961c`,
      `e2e-testing@5ef69c5` — the other 19 baselined/tracked repos already matched the current SSOT, apparently from an
      earlier unrelated full-template sync). PM itself is excluded from the automated rollout by design
      (`rollout-workflow-templates.sh`: "PM owns the templates -- skip self") and its own hand-maintained live copy had
      independently drifted too — surgically patched just the `|| true` line (`unified-trading-pm@39abe46b8`),
      deliberately preserving its pre-existing, unrelated `runs-on: ubuntu-latest` customization (vs. the template's
      `[self-hosted, glue]`) rather than blanket-overwriting it, since that wasn't part of this bug. All 6 touched repos
      shipped via the standard Pass-1 `quality-gates.sh` → Pass-2 `quickmerge --agent` flow and SHA-verified as
      ancestors of `origin/live-defi-rollout` post-push (not just trusting quickmerge's own "Landed" message, per this
      doc's own established discipline). Verified done-criterion: a fleet-wide grep for the fix line across every repo's
      live `main-backmerge-to-ldr.yml` confirms 0 repos still carry the pre-fix content;
      `detect_template_drift.py --workflows` `current_drift` for this template now shows only
      `unified-trading-pm/main-backmerge-to-ldr.yml` — confirmed via direct diff that residual entry is exclusively the
      pre-existing `runs-on` line, not the bug. Session survived a mid-task session death (uncommitted local edits for 3
      of the 5 auto-rollout repos plus PM's manual patch were lost — only the 2 already-committed repos survived);
      recovered by re-running the (idempotent) rollout script and re-applying the PM patch before re-committing, see
      `worker.md`'s resume contract. Host load fluctuated 9-28 (16 vCPU) throughout, consistent with this doc's standing
      "fluctuating-but-still-elevated, not resolved" characterization — no QG failures attributable to contention this
      pass.
- [ ] [BACKEND] P1. **New, opened by the 2026-07-31 ~15:17-15:26Z synchronized-multi-slot-kill corroboration below —
      main-agent-corroborated CPU-oversubscription, a distinct signature from the IO/disk-full and RAM-exhaustion
      variants already tracked.** Build a MACHINE-ENFORCED shared-host QG concurrency gate: a host-level
      `flock`/semaphore in `quality-gates.sh` (or `base-service.sh`) that blocks any run past `max(2, floor(cores/4))`
      concurrent full QG passes on one host — whether local AO-slot-worker QGs or self-hosted CI-runner QGs — so runs
      structurally cannot stack 13-deep the way they did at 2026-07-31~15:38Z (13 concurrent `quality-gates.sh` + 8
      `pytest` processes live, cap=4, violated 3x+ on the QG count alone — corroborated independently by both a
      review-agent session and main agent `agt-40d0ed` on-host). Self-discipline (the shared-host QG-sweep-batching rule
      in CLAUDE.md) is clearly not holding under load; this needs a structural block, not another documented violation.
      Done when: a concurrent QG run past the cap is measurably refused/queued (not just logged) on this host, verified
      by deliberately launching cap+1 QG passes and observing the (cap+1)th block until a slot frees.
- [ ] [DOCS] P3. **New, opened by the same corroboration — a `boot_read_unconfirmed` gap hit firsthand this session.**
      `review.md`'s own "Boot — read the canonical files first" section names only `RULES.md` as the required pre-poll
      read; it never explicitly lists `worker.md`, yet the live `/api/slots/<N>/boot` endpoint's required-file check
      DOES enforce `worker.md` for the review role — confirmed directly: this session's own first `/boot` call was
      rejected 428 (`"missing": ["...agents/worker.md"]`) even after declaring `RULES.md` + `review.md` read
      (`GET /api/activity?slot=1` event `boot_read_unconfirmed` at 2026-07-31T18:04:34Z is this exact rejection). Add
      `worker.md` to the explicit required-pre-read list in both `review.md`'s boot section and `RULES.md` (wherever it
      enumerates per-role required reads), so a fresh review session's own docs tell it the true required set instead of
      discovering it via a 428 round-trip. Done when: `review.md` explicitly names `worker.md` as a required STEP-0/1
      read, and the documented set matches the server's actually-enforced set for role=review.

## Evidence

- Live query: `GET http://localhost:8765/api/escalations/active?include_resolved_within_hours=6` via SSM against
  `i-0c9b283b31d6b5ca7`, 2026-07-29T01:05:17Z and T01:08Z snapshots (raw JSON captured in this session's tool output,
  not reproduced here in full — re-run the same query for a fresh sample).
- Original doc: `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (1000 lines, at
  cap as of this writing).

## Progress Log

- **2026-07-29 (cicd escalation `agt-575a4c`, slot 3)**: corroborating data point for the P2 "re-measure protected-6
  post-resize" todo above. `instruments-service` PR #1012 (LDR→main promote, created 2026-07-29T04:49:40Z) hit
  `ldr_qg_failure` — checks-leg `QG_SLICE=typecheck` timed out (`exit=124`, run
  [30423320298](https://github.com/IggyIkenna/instruments-service/actions/runs/30423320298), ~04:52-04:54Z) while the
  SAME job's `QG_SLICE=lint-codex` selector independently printed "ALL QUALITY GATES PASSED" — confirms the failure was
  isolated to the typecheck selector, not a codex-compliance/lint regression (3 pre-existing tolerated violations —
  `sports_reference_fixtures.py` 914L file-size + a `process.py` function-size violation since fixed — sat within
  `CODEX_MAX_VIOLATIONS=3` in both this and later runs; the file-size violation is still present today and non-blocking,
  a red herring). Tests-leg failed independently in the same run via a pytest-xdist
  `RuntimeError: Unexpectedly no active workers available` AFTER all 1176 tests had already passed — a worker-teardown
  crash, not a test failure. Self-healed with no code change: PR #1012 closed, and 8 subsequent promote-PR incarnations
  (#1013, #1015, #1017-#1020) merged clean over the following ~10h, with the latest direct `live-defi-rollout`
  push-triggered run (`30462644516`, 2026-07-29T14:47:46Z) green — `QG_SLICE=typecheck` PASSED in 9s (vs.
  ~2min-before-timeout in the failing run), consistent with transient host contention, not a code regression. No fix
  applied (none needed — nothing is currently broken); filed as evidence for the re-measurement todo, not as a fresh
  unresolved occurrence.

- **2026-07-29 ~20:45Z (cicd escalation `agt-eda323`, slot 14)**: a DIFFERENT failure signature than every entry above —
  not host-contention-during-real-execution (timeouts, uv cache races, worker-teardown crashes), but the gate never
  starting at all. Dispatched to fix `instruments-service`#1025 (LDR→main promote) `ldr_qg_failure`; found
  `content-gate` ("content sentinel") + the `quality-gates-v2` aggregation job (both still hardcoded
  `runs-on: ubuntu-latest` in `python-quality-gates-v2.yml` — never migrated by either Wave-1 or Wave-2, which only
  touched `qg-slices` and the CALLER template's escalate/notify/dispatch jobs) failing in 2-3s with **zero steps and
  zero log blob**. Confirmed via `GET .../actions/runs/<id>/timing`: `"billable":{"UBUNTU":{"total_ms":0,...}}` for all
  4 ubuntu-latest jobs across two separate attempts (PR-triggered `30477967414` @18:00Z and a `workflow_dispatch` retry
  `30479612102` @18:22Z), while the SAME runs' self-hosted `[self-hosted, glue]` jobs (escalate-ldr-qg-failure,
  notify-ci-watcher) succeeded normally (runner `glue-ip-172-31-5-118-1`, confirmed online + idle both times).
  `QG slice` (the job that runs the actual test/lint/type work) was SKIPPED both times — i.e. **the real gate never ran;
  there is no code defect to fix**. GitHub status page checked live: Actions fully operational (only Copilot degraded) —
  rules out a platform incident. Widened the check fleet-wide: `agent-orchestrator`, `deployment-service`,
  `unified-trading-pm`, `market-data-processing-service`, `features-service` all show the SAME pattern on their most
  recent runs (19:20-20:45Z), and it has escalated over the evening from partial (only the ubuntu-latest jobs within a
  mixed run fail) to full run-level `startup_failure` with `total_count: 0` jobs (e.g. `unified-trading-pm` run
  `30489671842`, `agent-orchestrator` run `30487051711`) — nothing is even being scheduled for these workflows now, not
  just the QG reusable one. Working theory (not yet operator-confirmed): the retry-storm volumes this doc already
  documents (46 + 78 + many more `ldr_qg_failure` attempts fleet-wide) plus PM's own still-not-migrated Tier-B pipeline
  files (`ldr-to-main-promote(-fleet)`, `sit-gate`, etc. — all still `ubuntu-latest` per this doc's sibling
  `gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`) have now burned through the account's GitHub
  Actions spending limit for GH-hosted (ubuntu-latest) runners specifically — self-hosted jobs are unaffected because
  GitHub doesn't bill/gate self-hosted runner minutes at all, which is exactly the asymmetry observed. **If confirmed,
  this blocks EVERY repo's promotion pipeline fleet-wide right now, not just instruments-service#1025** — filed
  `BLK-21d55fb1` (task `agt-eda323`) to the dashboard for operator/main-agent decision (check/raise the GH Actions
  spending limit vs. migrate the remaining ubuntu-latest jobs to the already-oversubscribed self-hosted pool) rather
  than attempting a code "fix" for a gate that was never actually exercised. No code changed on `instruments-service`;
  slot left clean on `live-defi-rollout`.

- **2026-07-29 ~20:56Z (cicd escalation `agt-0cd704`, slot 9) — corroboration, pins down onset + one more affected PR**:
  dispatched to fix `ldr_qg_failure` on `unified-api-contracts` promotion PR #796. The ORIGINAL wall (`QG slice (tests)`
  failing a `uv` build-isolation step, "No such file or directory (os error 2)") was transient host contention, already
  refuted as a code issue by a same-commit `workflow_dispatch` success 8 min later (16:31:50Z, zero commits in between).
  Attempting to re-gate the PR head hit the SAME full run-level `startup_failure` (0 jobs) this doc's prior entry
  describes — 3 separate `workflow_dispatch` attempts on `unified-api-contracts`, plus one on `unified-trading-pm`'s
  `ldr-to-main-promote-fleet.yml`, all `startup_failure`/0 jobs. Swept `unified-trading-pm`'s run history back through
  100+ runs to pin the exact onset: **last success `2026-07-29T18:25:50Z` (`repository_dispatch`) → first failure
  `2026-07-29T18:27:24Z` (`schedule`)** — a hard transition, not a gradual degradation, and every run of every trigger
  type has failed continuously since. Runners confirmed `online`/idle (not busy) on `unified-trading-pm`,
  `agent-orchestrator`, `unified-api-contracts` — rules out runner-side unavailability as the mechanism for the
  full-run-level failures. Not re-filing `BLK-21d55fb1` (same standing condition, already escalated by `agt-eda323`) —
  adding this only as corroboration + the precise onset timestamp, which the prior entry didn't have. `#796` stays
  blocked on this fleet-wide incident clearing; no code fix applies. Pinged the authoring slot with this outcome; slot
  left clean on `live-defi-rollout`, no repo touched beyond this doc.

- **2026-07-29 ~21:00Z (cicd escalation `agt-dfdd5b`, slot 5)**: independent corroboration, escalated for
  `client-reporting-api` `ldr_qg_failure` (`#0`, no PR — a plain LDR-direct wall). Reproduced locally FIRST per the boot
  instructions: `bash scripts/quality-gates.sh` at HEAD `ed6586b8` — 665 passed, 4 skipped, 71.56% coverage,
  `ALL QUALITY GATES PASSED (59s)`, zero failures. The code and tests are clean; the wall is CI-only. Checked the actual
  failing CI run (`30479590370`, 18:22:09Z, the one that fired this escalation): `content-gate` + both `qg-slices` legs
  (`checks`, `tests`) all `success`, but the `quality-gates-v2` aggregation job itself failed in 12s despite its
  `needs.qg-slices.result` being `success` — logs for that job already 404'd (expired) by the time I looked.
  Re-dispatched fresh (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) three times across a ~10min
  window: all `startup_failure`, 1s, zero jobs. Widened the check myself (independently of `agt-eda323`'s own fleet
  check above, before finding this doc): `market-tick-data-service` and `instruments-service` fresh dispatches both
  `startup_failure` identically — and critically, `unified-trading-library` (NOT on the self-hosted-runner allowlist,
  `self_hosted_runner_labels: ""` i.e. `ubuntu-latest`-only, whose own dispatch succeeded cleanly at 16:31:54Z earlier
  today) now ALSO fails `startup_failure` on a fresh dispatch — ruling out "self-hosted pool contention" as sufficient
  explanation on its own (a pure-`ubuntu-latest` repo is affected too) and confirming this is the account-wide
  GH-hosted-runner spending-limit block `agt-eda323` already diagnosed, not something self-hosted-specific. Checked
  githubstatus.com independently: Actions component "Operational" (only a Copilot model-provider degradation listed) —
  platform-side incident ruled out again. **No code or workflow change made or needed on `client-reporting-api`** —
  filing my own bounded `/blocked` for escalation `agt-dfdd5b` referencing this doc + `BLK-21d55fb1` rather than
  duplicating the operator page; if unanswered within the 2-min bound, stopping per the one-shot contract. Slot left
  clean on `live-defi-rollout` (no branch changes made).

- **2026-07-29 ~21:20Z (cicd escalation `agt-614695`, slot 15) — DIFFERENT from every entry above: a real, separate
  local test regression, not pure infra**. Dispatched for `instruments-service` `ldr_qg_failure` (`#0`). CI showed the
  same fleet-wide `startup_failure` (0 jobs, 0 billable ms, confirmed via `.../actions/runs/<id>/timing`) this doc
  already tracks — but per the boot contract I also reproduced locally FIRST, and unlike `agt-dfdd5b`'s clean repro,
  `bash scripts/quality-gates.sh` at HEAD `4c05f2d3` genuinely failed: 10 failed / 5034 passed. Root-caused as
  cross-repo editable-dependency drift (`unified-api-contracts@0c0f6953` registered `FRED` as a new tradfi venue +
  `ohlcv_1d` as a genuine tradfi data_type) breaking two stale instruments-service test-side assumptions: (1) 9 tradfi
  v2 enumerator tests in `test_enumerate_expected_universe_v2.py` relied on `ohlcv_1d` silently passing through
  `_row_data_types`' unknown-data_type escape hatch to dodge NASDAQ/ETF's validity matrix + the MVP data_type-narrowing
  gate — now a real registered data_type, the passthrough no longer applies and row_dts collapsed to empty; (2)
  `test_pipeline_e2e_prediction.py`'s pinned `_PER_AG_TARGET_COUNTS["TRADFI"]` (7) went stale vs. the real UAC registry
  (now 8 venues). While diagnosing, discovered `slot-14` had independently found + fixed the identical root cause
  moments earlier (`instruments-service@7f272911`, "fix(tests): update tradfi test fixtures for FRED's ohlcv_1d/venue
  registration") — my own from-scratch fix converged on the same data_type swap (`ohlcv_1m`) and the same count bump
  (7→8), confirming the diagnosis independently. Discarded my redundant local changes in favor of the already-landed,
  already-verified commit (`git checkout HEAD --` on both files) rather than force a duplicate/conflicting push.
  Re-verified at current HEAD: `ALL QUALITY GATES PASSED (93s)`, 5044 passed / 0 failed. **This underlying test
  regression is now fully fixed on `live-defi-rollout`** — the residual CI red on this repo is purely the ongoing
  fleet-wide `startup_failure` incident this doc already tracks (`BLK-21d55fb1`), not re-filing it. Pinged
  `AUTHORING_SLOT=ci-reconcile` with the outcome. Slot left clean on `live-defi-rollout`, no branch changes beyond the
  (already-shipped) fix confirmed.

- **2026-07-29 ~23:38Z (cicd escalation `agt-28375c`, slot 1) — 3rd independent confirmation for `instruments-service`:
  the `agt-614695` test-regression fix holds, residual red is pure infra**. Re-dispatched against the same standing
  `instruments-service` `ldr_qg_failure` wall (`#0`, no PR; this escalation alone was already at `attempts: 4` per
  `GET /api/escalations/active` before this run — one of several duplicate concurrent escalations for this repo,
  `agt-4b4ba8`/`agt-614695`/`agt-d04227`/`agt-28375c`, all `still_red_reescalated` from prior rounds). Reproduced
  locally FIRST per the boot contract, backgrounded per the mandatory non-blocking pattern (never foreground — 15-min
  heartbeat-silence kill risk): `bash scripts/quality-gates.sh` at HEAD `7f272911` (the exact fix commit `agt-614695`
  already verified) — `5044 passed, 7 skipped`, coverage `88.77% ≥ 88.0%` floor, `ALL QUALITY GATES PASSED (99s)`,
  sentinel written matching HEAD. Zero failures; nothing left to fix on the code/test side. Fresh CI check: 3 most
  recent `live-defi-rollout` runs (23:35:55Z, 22:14:38Z, 22:01:22Z) all `startup_failure`; confirmed `jobs: []` +
  `timing.billable: {}` + `run_duration_ms: 1000` on the newest (`30500040561`) — identical zero-job signature to every
  other repo this doc and `github_actions_billing_wall_recurrence_2026_07_29.md` track. Also checked the PUSH-triggered
  run for the fix commit itself (`30492395057`, `headSha=7f272911...`, 21:26:43Z, 0s): same `startup_failure`/`jobs:[]`
  signature — the fix commit was never able to prove itself green on CI because the wall was already up by the time it
  landed, not because the fix is incomplete. **No code or workflow change made or needed.** `GET /api/repo-blockers` →
  `open: []` (none registered for this repo, nothing to fast-path). Not re-filing `/blocked` (same standing
  `BLK-21d55fb1` condition; the `[OPERATOR] P0` in `github_actions_billing_wall_recurrence_2026_07_29.md` already covers
  the decision — avoiding the escalation-spam pattern that doc's own P3 todo flags). Not pinging the authoring slot
  (`AUTHORING_SLOT=ci-reconcile`, the confirmed non-numeric literal that 400s per the entries above and the sibling
  doc's evidence log). Slot left clean on `live-defi-rollout`, working tree clean, no branch changes.

- **2026-07-30 ~06:20-06:27Z (operator-ruling close-out pass)**: Attempted the P2 "re-measure protected-6 retry-attempt
  counts post-resize" todo. `curl http://localhost:8765/api/escalations/active?...` via SSM against
  `i-0c9b283b31d6b5ca7` **timed out** (`curl --max-time 20` → exit 28, `HTTP_STATUS:000`) on both the original unbounded
  attempt (never returned in ~10min, abandoned) and a bounded 20s retry — the AO escalations API itself is currently
  unresponsive on this box, so the literal attempt-count metric this todo asks for could not be pulled. Fell back to
  direct host-level measurement (same SSM channel), which answers the todo's underlying question directly without
  needing the API: `cat /proc/loadavg` → **97.38, 93.02, 78.15** (1/5/15-min load) on a confirmed **16-vCPU** box
  (`nproc`) — i.e. ~6x oversubscribed, not a transient spike (5-min and 15-min averages are both severely elevated too).
  Confirmed this IS the post-resize box, not a stale reading: `aws ec2 describe-instances` shows `i-0c9b283b31d6b5ca7`
  is `m8i.4xlarge` (16 vCPU / 64GB), `LaunchTime=2026-07-29T04:47:41Z` — launched the same day as the ruling's
  "just-applied host fix," so this measurement genuinely reflects the resized instance, not the pre-fix box.
  `ps -eo pid,pcpu,pmem,etimes,comm --sort=-pcpu` top-12: a mix of `python3` (the AO server itself, PID 4051394, 68%
  CPU) and **10 separate `claude` processes each at 39-68% CPU** — i.e. roughly a dozen concurrent AO-slot/agent
  sessions actively burning CPU simultaneously on this one box, consistent with (not less than) the original doc's
  "13-20 concurrent AO slot-worker sessions" figure. `pgrep -fc "Runner.Listener"` → **33** self-hosted GitHub Actions
  runner processes — MORE than the original doc's "up to 22 self-hosted CI runner pools" figure, not fewer; `free -h` →
  `Swap: 47Gi total, 21Gi used` — heavy swap usage persists (the "added swap" half of the fix is in place and is
  genuinely being drawn on, which is itself a symptom of memory pressure, not evidence the pressure is resolved).

  **Verdict: NEGATIVE — the post-resize host fix has NOT resolved the contention.** Load average ~6x the box's CPU
  count, 33 live self-hosted runners (up from ~22), a dozen concurrent `claude` sessions, and 21GB of active swap usage
  are a more severe oversubscription signature than the original incident's own numbers, not an improved one. This
  directly satisfies this todo's own stated trigger ("if 46/78-style escalations recur despite the host fix... that is
  the trigger to revisit reverting protected-6 to GitHub-hosted runners") — even without the literal escalation
  attempt-count (blocked by the unresponsive API, itself corroborating evidence of the same overload), the host-level
  picture is unambiguous. Recommend the next session/operator treat "revisit reverting protected-6 to GitHub-hosted
  runners" as the live decision now due, rather than continuing to await a clean post-resize confirmation that this
  measurement shows will not arrive on the current box as configured. Not making that reversion call myself — it is a
  real production-topology decision (which repos' CI moves back to GH-hosted, cost/perf tradeoff), not a mechanical
  follow-up of an already-made ruling, so left for the operator per this session's own scope (execute already-decided
  rulings, don't make new policy calls). No code/infra change made; read-only SSM queries only.

- **na-eligibility-audit 2026-07-30** (tranche=cross-cutting, autonomous): RECLASSIFY NA → planning — the 4 remaining
  todos are bounded measurements/diagnostics (attempt-count distribution over a stated window, post-resize protected-6
  re-measure, plan_health-queue root-cause split, doc split); the one operator call is already `[x]` ruled. **Note
  (integrator, same day)**: the close-out pass recorded immediately above already executed the post-resize protected-6
  re-measure and returned a NEGATIVE verdict, so that particular todo is answered even though its checkbox is untouched
  here.

- **2026-07-30T10:54-11:05Z (slot 5, data_engineering) — P1 cost-quantification todo, real numbers**. Two real,
  independently-sourced datasets, not assumed:

  **(1) Escalation attempt-count distribution — pulled directly from the AO's SQLite `state.db`
  (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`, read-only query), NOT the
  `/api/escalations/active` HTTP endpoint.** Confirmed via code read (`server/escalation.py:list_active_escalations`,
  line ~1804) that the endpoint hard-caps at `.limit(100)` rows ordered by `created_at DESC` REGARDLESS of the
  `include_resolved_within_hours` window passed — verified empirically too (`include_resolved_within_hours=72` and
  `=200` both returned exactly 100 rows, earliest `created_at` unchanged at `2026-07-29T06:27:48Z` either way). This
  means the endpoint structurally CANNOT answer "full 2026-07-27→present window" once total escalation volume (all
  wall_types) exceeds 100 in that window — which it does (100 rows only reached back ~28h, not the ~83h this todo
  needs). Querying `escalation_queue` directly instead: **168 `ldr_qg_failure` escalations created since
  2026-07-27T00:00:00Z** (status: 125 `resolved`/`qg_v2_green`, 28 `unresolved`/`still_red_past_deadline`, 9
  `dispatched`/`still_red_reescalated`, 6 `dispatched` mid-flight). Attempts: **min 1, max 224, mean 4.85, sum 815**
  across the 168 rows. Distribution is heavily right-skewed: 76 rows at exactly 1 attempt, 51 at 2, 22 at 3, tapering to
  a long tail of 12 escalations at ≥5 attempts including the extremes already known from prior entries in this doc
  (`trading-agent-service`#364 = 78, `market-tick-data-service`#0 = 46) PLUS one NEW extreme not previously surfaced:
  **`instruments-service`#1009 (`agt-1b4cc2`) hit 224 attempts** before resolving `qg_v2_green` at 2026-07-29T09:59:49Z
  (created 2026-07-29T01:05:15Z, ~8h54m to resolve).

  **Attempts ≠ CI re-triggers — confirmed by direct cross-check, an important methodology correction.** Sampled the
  224-attempt `instruments-service`#1009 case against real GH Actions history
  (`gh run list --workflow=quality-gates-v2.yml --created "2026-07-29T01:00:00Z..2026-07-29T10:00:00Z"`): only **19
  actual CI runs** occurred in that ~9h window (11 success, 7 failure, 1 cancelled) — nowhere near 224. So
  `escalation.attempts` (incremented once per fix-worker DISPATCH, `escalation.py:647`) measures agent-RESPAWN churn,
  not CI-run churn; a naive "attempts × CI-run-cost" formula would have overstated GH-Actions waste by ~12×. Corrected
  the estimate below to use REAL CI run counts instead of escalation attempt counts.

  **(2) Real fleet-wide `quality-gates-v2` CI run volume since 2026-07-27, via `gh run list`/`gh api`** across the 25
  distinct repos carrying a `ldr_qg_failure` escalation in this window (queried per-repo with
  `--created "2026-07-27T00:00:00Z..2026-07-30T23:59:59Z"`; `unified-trading-pm` hit the 500-row page cap on a single
  query so it was re-split into 5 sub-windows and re-summed to get its true count — every other repo stayed under the
  cap on the first pass). **Grand total: 2,893 `quality-gates-v2` runs fleet-wide** — 2,269 success (78.4%), 322
  cancelled (11.1%), 255 failure (8.8%), 40 `startup_failure` (1.4%, the account-wide GH-hosted-runner spending-limit
  incident this doc's earlier entries already traced — `BLK-21d55fb1`), 7 queued/pending. Non-success (real retry churn)
  = 624 runs (21.6%).

  **GH-Actions-dollar estimate.** Confirmed via `gh api .../actions/runs/<id>/jobs` on a sample run (`30441834008`) that
  the residual, still-not-self-hosted-migrated jobs are 3 short `ubuntu-latest` jobs per run (`content sentinel`,
  `quality-gates-v2` aggregator, `Record QG result` — all ≤10s wall-clock but per the pre-existing migration doc's own
  established finding, `github_actions_self_hosted_runner_migration_2026_07_15.md:1386`, GitHub bills a **1-minute
  minimum PER JOB** regardless of the sub-10s actual duration the `timing` API rounds to `0ms`). Confirmed
  `startup_failure` runs bill
  **$0** (0 jobs ever scheduled, matching this doc's earlier `billable: {}`/`jobs:
  []` findings). At the confirmed **$0.006/min**
  rate (`github_actions_cost_reduction_options_analysis_2026_07_15.md`): real-dispatched non-success runs (cancelled
  322 + failure 255 = 577; excluding the 40 zero-job `startup_failure` runs) × 3 jobs × 1 min × $0.006/min = **~$10.39**
  in GH-Actions-dollar waste from actual retry/cancel churn over this ~3.5-day sampled window — extrapolated (if this
  rate held for a full month, which it may not since this is an active incident, not steady-state): **≈$85-95/mo**.

  **Verdict vs. the migration's original projected savings.** The archived migration plan's own stated target: fleet
  **~$1,000/mo → ~$550-650/mo** (i.e.,
  **~$350-450/mo projected savings**,
  `github_actions_self_hosted_runner_migration_2026_07_15.md` Progress Log). The retry storm's GH-Actions-dollar waste
  (~$85-95/mo
  if sustained) is **real but small — roughly 2-3% of the projected savings, not big enough to threaten or erase the
  migration's net benefit in GH-Actions-billing terms.** This is the mechanical, non-obvious reason: the migration moved
  the expensive, long-running `qg-slices` (test/typecheck) work to self-hosted runners, which GitHub does not bill at
  all — so even a large volume of RETRIED runs only re-bills the tiny residual 3-job hosted overhead, not the real
  compute. The operator's original framing ("retry churn may be burning more wall-clock/compute than the GH minutes it
  saved") is directionally correct, but the expensive resource it's pointing at is **AWS EC2 wall-clock/compute on the
  oversubscribed shared host** (`i-0c9b283b31d6b5ca7`, real cost, NOT GitHub-Actions-billed) from the 815 real
  agent-dispatch attempts — a genuinely different cost bucket than "GH-Actions-minutes," which this todo's literal
  framing didn't cover and which this session did NOT quantify (opened as a new `[DATA] P2` follow-up todo above rather
  than assumed away). No code/infra change made; read-only SQLite + `gh api`/`gh run list` queries only; slot left clean
  on `live-defi-rollout`.

- **2026-07-30 ~08:44Z (cicd escalation `agt-08a769`, slot 9) — corroboration, `client-reporting-api` promotion PR
  #609**: dispatched for `ldr_qg_failure` (`quality-gates-v2` red on the LDR→main promote PR, run
  [30526015130](https://github.com/IggyIkenna/client-reporting-api/actions/runs/30526015130)). Diagnosed the exact
  failure: `QG slice (checks)` job's `QG_SLICE=typecheck` selector hit the hard 120s basedpyright timeout
  (`Type check FAILED/timeout (exit=124)`, `08:20:25Z→08:22:25Z`) — same signature this doc already tracks fleet-wide.
  Reproduced locally FIRST: `QG_SLICE=typecheck bash scripts/quality-gates.sh --no-fix` at the same HEAD completed
  cleanly and fast (133 pre-existing basedpyright warnings, no error ceiling set, `QG_SLICE=typecheck PASSED`) —
  confirms the code is clean and the wall is CI-host-contention only, not a regression. By the time this was diagnosed
  the pipeline had already self-healed with no code change: PR #609 merged at 08:16:02Z (merge commit `d5ebf83a`), a
  fresh `workflow_dispatch` retrigger on `live-defi-rollout` (`30526108370`, 08:17:26Z) went green, the next promote PR
  #610 merged cleanly at 09:16:04Z, and the current `live-defi-rollout` HEAD (`e1b3106`) is green (`30535642575`,
  10:41:33Z). No open PRs, no open repo-blockers for this repo. **No code or workflow change made or needed** — filing
  as another corroborating data point for the box-contention root cause, not a fresh unresolved occurrence. Slot left
  clean on `live-defi-rollout`.

- **2026-07-30 ~15:48Z (review agent `agt-2552a2`, slot 1) — corroboration, mass `tmux_session_lost` cluster
  (2026-07-30T14:54-15:01Z) + a concrete double-requeue**: independently re-verified (not just relayed from a prior
  session's chat) via `GET /api/activity?limit=500` against the live orchestrator API. Three back-to-back kill waves in
  ~7 minutes: **14:54:09Z** — slots 1, 5, 9, 11 all `tmux_session_lost`→`killed` in the same second (slot 5 released
  `sports_odds_api_scattered_multiyear_gaps-002`, slot 9 released `mtds_plan_flip_fabricated_commit_sha_evidence-002`,
  slot 11 released `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003`); **14:58:13Z** — slots 1, 4 killed again;
  **15:01:32Z** — slots 1, 10 killed, slot 10 releasing `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003` — the SAME
  task id slot 11 had just released 7m23s earlier, i.e. a genuine double-requeue-in-7min of one task (real rework, not
  retry-churn noise). Notably slot 1 itself (this review agent's own slot) was killed in all three waves (14:54:09Z,
  14:58:13Z, 15:01:32Z) — direct first-hand evidence this session's predecessor review agent (`agt-4daef9`) was a
  casualty of the same cluster, which is why this is a fresh review session picking the thread back up. **Current host
  reading** (2026-07-30T15:48:40Z, `uptime`/`free -h` on the box this session runs on): load average 11.94 / 20.27 /
  21.63 (1/5/15-min) on 16 vCPUs — 1-min has eased under the ~26.20/16vCPU peak cited earlier today, but the 15-min
  average is still ~135% of core count, so this reads as fluctuating-but-still-elevated contention, not resolved; swap
  14Gi/47Gi used (same order of magnitude as the ~16Gi cited earlier). **OOM-mechanism stays UNCONFIRMED** — this
  session has no root and did not check `dmesg`/`journalctl -k`, so the swap+load pressure is "consistent with memory
  pressure" only, not an asserted OOM-kill cause (see the new `[OPERATOR]` todo above for the kernel-log follow-up this
  needs). **Recommend** (not actioned — plan-owner's call, not mine): this is the second corroboration entry landed in
  under 12h (after the 08:44Z one above); the L150 `[SCRIPT] P2` doc-split todo is worth pulling forward given entries
  keep accumulating. No code or plan-structure change made; slot 1 left clean on `live-defi-rollout`.
- **2026-07-30T16:39Z (review agent `agt-f99b61`, slot 1) — a FRESH, LARGER `tmux_session_lost` wave than the one above,
  third corroboration entry today**: independently re-verified via
  `GET /api/activity?type=tmux_session_lost &since=2026-07-30T14:00:00Z` (not relayed) — **~18 kill events across 12
  distinct slots (1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14) within a 26-minute window (16:09:24Z–16:35:39Z)**, wider
  blast radius than the 14:54-15:01Z cluster this doc already tracks (6 slots, ~8 kills in 7min). Several kills forced a
  genuine task requeue (real rework, not retry-churn): slot 9 released `prediction_satellite_ao_dispatch_batch6-004`,
  slot 10 released `cefi_satellite_ao_dispatch_batch1_finalize-004`, slot 4 released
  `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero-003` (again — see the prior corroboration entry's double-requeue note
  for this same task id) then again `cefi_track2_backfill_vm_preempted_no_recovery-001`, slot 5 released
  `sports_odds_api_scattered_multiyear_gaps-002` then `tradfi_satellite_ao_dispatch_batch5-014`, slot 12 released
  `cefi_track2_coverage_backfill_checkpoints_finalize-001`, slot 13 released
  `prek_patch_cache_replays_stale_diff_onto_unrelated_files-003`, slot 11 released
  `prediction_satellite_ao_dispatch_batch6-004`. Slot 1 itself (this review agent's own slot) was killed 3 times in this
  window (16:21:52Z, 16:23:56Z, 16:29:01Z) — all BEFORE this session (`agt-f99b61`) successfully registered at
  16:32:42Z, i.e. this is why the queued main-agent messages from ~15:10-15:54Z sat unanswered for over an hour: the
  review role's slot kept getting killed on respawn, not just the one predecessor session (`agt-2552a2`) already
  attributed to the earlier 14:54-15:01Z wave. **Current host reading (16:39:44Z, this box) is EASED, not worse**:
  `uptime` load average 7.66/8.79/11.57 (1/5/15-min) on 16 vCPUs — 1-min now comfortably under core count, versus the
  97.38/93.02/78.15 reading at 06:20Z and the 26.20/16vCPU peak cited earlier today; `free -h` swap 8.6Gi/47Gi used,
  down from the 14-21Gi range cited in the two entries above. **Read together with the eased current snapshot, this
  looks like another acute burst that has already subsided, not a sustained worsening trend** — consistent with this
  doc's standing "fluctuating-but-still-elevated" characterization, just a bigger individual burst than the last one.
  Flagged to main agent (`agt-fd75de`) for awareness per its own standing re-flag trigger ("task-holders start getting
  kicked repeatedly"); no operator page requested (bursty-not-steady-state read, same disposition as the prior
  corroboration). No code or plan-structure change made; slot 1 left clean on `live-defi-rollout`. **Addendum (main
  agent `agt-fd75de`, independent real-time confirmation)**: main was tracking this exact window tick-by-tick from the
  fleet side and confirms the burst-not-worsening read directly — killed count climbed to 5-6 with ZERO `worker_kicked`
  events (this wave is `tmux_session_lost` host/session-churn self-healing via AutoSpawn, a distinct failure class from
  a watchdog `worker_kicked` stuck-worker intervention — no watchdog fired here), commits kept landing throughout
  (<2min-old commits verified across the window), and the fleet fully recovered to working 11-12 by ~16:41Z. Escalation
  bar (commits→0 sustained, OR task-holders getting `worker_kicked` repeatedly) was not met by either measure. Net: a
  wider-radius host-pressure burst that already self-healed, not 12 stuck workers.

- **2026-07-30 ~16:44Z (cicd escalation `agt-7bcf55`, slot 3) — corroboration, `features-service` LDR-direct wall, both
  slices affected simultaneously**: dispatched for `ldr_qg_failure` (`#0`, no PR) at `live-defi-rollout` commit
  `6d4a9374` (a `main`→`_backmerge` merge commit). Unlike most entries above, BOTH slices failed in the same run
  ([30547641524](https://github.com/IggyIkenna/features-service/actions/runs/30547641524), 13:35:54Z):
  `QG slice (checks)` hit the hard 120s basedpyright timeout (`Type check FAILED/timeout`, exit=124, 13:38:51→13:40:51Z)
  and `QG slice (tests)` independently hung mid-execution inside `test_adx_columns_present` (stack paused inside pandas
  `Series.std()`→`nanops.nanvar`), killed by pytest-timeout's thread-based dumper after ~11min (13:43:44→13:54:52Z) — a
  genuine in-process stall, not a subprocess-launch failure like the MEM_WRAP/D-Bus signature this doc tracks elsewhere.
  Diagnosed the code was clean BEFORE assuming a fix was needed: `git diff` between the last-green commit (`48f77f2a`,
  run 30543191133 @12:35:38Z) and the red commit (`6d4a9374`) is **byte-identical, zero diff** — ruling out a code
  regression outright regardless of which slice is examined. Reproduced the specific failing test locally
  (`test_momentum.py::TestMomentumCalculate::test_adx_columns_present`): passes clean in 6.21s, no hang. A second CI
  attempt on the same unchanged code
  ([30553419354](https://github.com/IggyIkenna/features-service/actions/runs/30553419354), 14:47:10Z) failed again (same
  signature) — ruled out a one-off fluke, this was sustained contention, not a single bad sample. A third attempt
  ([30558943290](https://github.com/IggyIkenna/features-service/actions/runs/30558943290), workflow_dispatch, 15:54:03Z,
  same commit now at HEAD `f0fc6f2e`) came back fully green — `checks` passed in ~2min, `tests` took ~50min wall-clock
  but `conclusion: success` — direct proof the wall was transient host contention, not a defect, once contention eased.
  **No code or workflow change made or needed.** `GET /api/repo-blockers` → none open for `features-service`. Slot left
  clean on `live-defi-rollout`, no branch changes.
- **2026-07-30 ~19:55Z (cicd escalation `agt-96bec9`, slot 8) — 2nd same-day `features-service` corroboration, both
  slices again, this time on the LDR→main promotion PR itself**: dispatched as `ldr_qg_failure` for promotion PR `#902`
  (`live-defi-rollout` → `main`), failing run
  [30569658808](https://github.com/IggyIkenna/features-service/actions/runs/30569658808) (`pull_request` event on
  `promote/features-service/edf80c88beb8`, created 18:16:08Z). Same dual-slice signature as `agt-7bcf55`'s entry
  directly above, ~5h later same day: `QG slice (checks)` hit the hard 120s basedpyright timeout
  (`Type check FAILED/timeout`, exit=124, 19:04:01→19:06:02Z) and `QG slice (tests)` independently hung mid-execution
  inside `test_regime_clustering.py::TestFitAndAssignPerTimeframe::test_returns_result_for_each_timeframe` (stack paused
  inside `fit_regime_clusters` at `regime_clustering.py:182`, a plain list-comprehension over `feature_df.columns`, not
  a real hang point), killed by pytest-timeout's thread-based dumper after the 150s per-test budget (19:12:44→19:17:02Z,
  roughly 4m18s past the last completed test). Diagnosed the code was clean before assuming a fix was needed: the PR's
  own content (`edf80c88`, "fix(volatility,delta_one): project bare read_availability_index calls to actual column
  usage") touches only `volatility/`+`delta_one/` call sites — nowhere near
  `cross_instrument/app/calculators/regime_clustering.py` — ruling out a code regression by diff scope alone. Reproduced
  the specific failing test locally: `test_returns_result_for_each_timeframe` passes clean in 3.84s (tiny fixture, 50-80
  rows × 3 timeframes) — no plausible legitimate path to a 150s+ hang, matching this doc's established profile exactly.
  Host reading at investigation time: `uptime` load average 12.75/13.39/14.01 (1/5/15-min) on 16 vCPUs — still
  comfortably above core count, consistent with "fluctuating-but-still-elevated," not resolved; `ps aux` showed 3+
  concurrent self-hosted "glue" CI runners (features-service, instruments-service, alerting-service) plus ~10 concurrent
  interactive Claude sessions on the same box at once. **PR #902 was already `state=MERGED` at `18:16:11Z`** — 3 seconds
  after this failing run even started — the exact self-merge-via-independent-earlier-green- check pattern this doc
  already documents for instruments-service #1026/#1027/#1035: the failing `pull_request` run is orphaned noise against
  an already-merged PR, not a live blocker. Confirmed downstream promotion machinery succeeded independently:
  `main-backmerge-to-ldr` (run 30569667561) and `Semver Agent` (run 30569667555) both `conclusion: success` on the same
  push. `GET /api/repo-blockers` → none open for `features-service`; `gh pr list --state open` → empty. Two
  `quality-gates-v2` runs (`30569668743` push:main, `30570836256` workflow_dispatch on LDR) sat `status=queued` for
  1h38m+ at investigation time with zero conclusion — consistent with the same runner- capacity crisis this doc tracks
  (queue backlog, not a hang once picked up) — noted here as a data point, not separately actioned since nothing is
  blocked pending their completion.

- **2026-07-30 (slot 4, backend_engineer) — `plan_health` escalation-queue diagnosis, the P2 todo above**. Code read +
  direct live SQLite query against the orchestrator's own `state.db`
  (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db` — this session runs ON the
  orchestrator VM itself, `http://localhost:8765` is the live API, no SSM needed), not the `/api/escalations/active`
  endpoint (already known too small — `.limit(100)`, per the P1 cost-quantification entry above).

  **Ruled out "no matching plan_health worker type" — both by code and by data.** `server/escalation.py`'s `WALL_TYPES`
  includes `"plan_health"` (line ~67) and `_prompt_template_for()` (line ~116) routes it through the exact SAME fallback
  as `ldr_qg_failure`/`main_ci_red`/every other generic wall — the shared `"cicd"` boot-prompt template, spawned via the
  identical `escalate()`→`_pick_free_slot()`→`tmux_spawn.spawn()` path. There is no separate "plan_health worker type"
  to be missing; a plan_health escalation and an ldr_qg_failure escalation compete for slots identically. (Note:
  `server/plan_health.py`'s own `dispatch()`/`_pick_free_slot()` is a DIFFERENT thing — the daily
  plan-reconciler/ag-closeout/etc. AUDIT dispatcher, unrelated to the `wall_type="plan_health"` CI-escalation path this
  todo is about; same free-slot semantics, different call site, easy to conflate by name alone.) Confirmed empirically:
  `SELECT status, count(*) FROM escalation_queue WHERE wall_type='plan_health' GROUP BY status` → **all 214 rows ever
  created are `status='resolved'`, resolution=`qg_v2_green`, ZERO currently stuck** — a mechanically broken/missing
  worker type would show a growing pool of permanently-`queued` rows, not a 100% eventual-resolution rate.

  **The real mechanism: `plan_health` shares the SAME host-contention root cause as `ldr_qg_failure`, via a literal
  shared bottleneck in the dispatch code — not just "the same kind of problem."** Traced the actual source of
  `wall_type=plan_health` escalations first: `unified-trading-pm/.github/workflows/plan-health-agent.yml`'s
  `plan-health-gate` job fires on EVERY PM→main promotion `pull_request` (not `ldr-docs-gate.yml`'s hourly
  frontmatter-only check, which is a separate, rarer trigger with `pr_number: 0`) — this matches the issue doc's finding
  exactly (12 promote-PR incarnations #1740-#1751 in ~5h = one plan-health-gate run per regenerated promote PR). When
  `run_hygiene_sweep.sh --ci` finds HARD failures the deterministic auto-fix couldn't resolve, it dispatches
  `wall_type=plan_health` with the REAL `pr_number` via `escalate-to-orchestrator.yml`.

  On the orchestrator side, `escalate()` tries an immediate `_pick_free_slot()` dispatch at creation time; if no slot is
  free right then, the row is inserted `status='queued'` (never dropped — Gap 3 fix) and only re-attempted by
  `retry_queued_escalations()`, called once per `AutoSpawnLoop` tick (`server/autospawn.py:2485`, default tick interval
  60s via `autospawn_interval_seconds`). That function caps itself at **`RETRY_PER_TICK = 2`**
  (`server/escalation.py:979`) — oldest-`created_at`-first, but critically **shared globally across every `WALL_TYPES`
  value, not partitioned per wall_type**. The code comment states the tradeoff plainly: "escalations claim free slots
  BEFORE backlog tasks — CI walls are urgent — but a burst must not starve the task queue forever." Reasonable in
  isolation, but during THIS doc's incident window, `plan_health` (44 active) and `ldr_qg_failure` (47 active) — 91
  combined — were both drawing from the identical 2-per-60s global retry budget, on top of the already well-documented
  host/slot scarcity (33 self-hosted runners + a dozen concurrent `claude` sessions on a 16-vCPU box). Empirical
  confirmation: `created_at`→`dispatched_at` gaps for `plan_health` rows during the burst window range from ~5 to ~12.4
  hours (e.g. PR #1754, `agt-f6a9b1`: created 01:42:37Z, not dispatched until 14:08:06Z — **745 minutes**, 298 recorded
  `attempts` — then resolved just 15 minutes after that dispatch finally landed), even though the OVERALL average
  `created_at`→`dispatched_at` gap across all 214 resolved rows is a much saner ~62 minutes
  (`avg((julianday(dispatched_at)-julianday(created_at))*24*60)` = 61.8) — i.e. the "44 active, growing, none resolving"
  snapshot the issue doc captured was a genuine acute tail spike during the worst of the incident, not the steady state,
  and it fully drained afterward (0 stuck now). The operator-flagged trio specifically
  (`agt-6a6ba6`/`agt-4c0ede`/`agt-4de402`, PRs #1746/#1747/#1748) DID resolve — dispatched ~43-51min after creation
  (matching the doc's own live check at the time), resolved a further ~59min after that (`qg_v2_green` at
  `01:33:3{5,6}Z`), so roughly 1h40m-2h50m total creation-to-resolution — slow, but not silently stuck, and now closed.

  **Verdict: same root cause (fleet-wide host/slot contention), not an independent bottleneck — but the PRECISE
  mechanism is more specific than "the host is busy": a hardcoded, wall-type-agnostic `RETRY_PER_TICK=2` throttle in the
  queued-escalation retry loop compounds pure slot scarcity into visibly long, uneven per-row dispatch delays during a
  multi-wall-type burst.** Opened a new `[BACKEND] P3` follow-up todo above (not fixing inline — this is a
  scheduling-policy tuning call, not a bug, and the existing 2-per-tick choice has a stated deliberate rationale worth
  an explicit ruling rather than a unilateral change) to revisit whether the cap should scale with queue depth or be
  partitioned per wall_type. No code changed this session — read-only SQLite query + code read only; slot left clean on
  `live-defi-rollout`. blocked pending their completion. **No code or workflow change made or needed.** Slot left clean
  on `live-defi-rollout`, no branch changes. clean on `live-defi-rollout`, no branch changes.

- **2026-07-30 ~22:36-23:17Z (cicd escalation `agt-5754dd`, slot 2, `wall_type=main_ci_red`) — 3rd same-day
  `features-service` corroboration, and the WORST single instance recorded in this doc so far: 4 consecutive full-suite
  `quality-gates-v2` attempts on the SAME unchanged commit, each failing at a DIFFERENT unrelated location, with host
  load climbing (not fluctuating-and-easing) across the session**. Dispatched for `features-service` `quality-gates-v2`
  RED on `main` (no PR -- a direct-push wall on the promotion merge commit itself, `13a23d8e`, "chore(promote): LDR ->
  main (Option-B direct)"). Diagnosed BEFORE assuming a code issue, per this doc's own established discipline:
  `git merge-base --is-ancestor origin/main origin/live-defi-rollout` -> main is a PURE ancestor of the reportedly-green
  LDR HEAD (`8e62dc30`, 334 commits ahead, 0 commits the other way) -- and confirmed zero diff on the failing test paths
  specifically (`base_calculator.py`, `test_regime_calculator.py`, `pyproject.toml`, `uv.lock` all byte-identical
  between the two branches). Ruled out both this wall's own classification options (PROMOTION STUCK / MAIN-ONLY stale
  workflow) -- this is neither; it is this doc's own already-tracked host-contention flake class, reproduced 4/4 times
  in a row:
  1. Original wall (run `30582695053`, first attempt): `QG slice (tests)` hung inside
     `test_regime_calculator.py::test_regime_calculator_no_forward_looking` at a `polars.join_asof(...).collect()` ->
     `get_engine_affinity()` call -- pytest-timeout thread-watchdog fired, faulthandler dump showed a live
     application-code frame, not a crash.
  2. 1st rerun: hung inside generic pytest fixture-resolution machinery (`_pytest/fixtures.py:_get_active_fixturedef` ->
     `pluggy` hook dispatch) -- **no application code frame at all**, the strongest possible signature for pure
     scheduling/descheduling starvation rather than a slow test.
  3. 2nd rerun: hung inside `tests/delta_one/unit/test_feature_groups/test_oscillators.py`, a third, unrelated location;
     progress through the suite was also visibly slower than the first attempt (16% reached after 6min vs. 56% after
     3min in attempt 1).
  4. 3rd rerun: hung inside `tests/delta_one/unit/test_feature_groups/test_momentum.py` -- a fourth unrelated location.
     Host load read at the end of each attempt tells the real story: **11.02/12.87/13.21 -> 14.09/14.03/13.59 ->
     17.23/16.18/14.77** (1/5/15-min, this box, presumably the same 16-vCPU host this doc already tracks) -- climbing
     across the ~40min session, not easing, with the final reading's 1-min average ABOVE the vCPU count. This is a more
     severe, actively-worsening instance than the two same-day `features-service` entries already in this doc
     (`agt-7bcf55` 13:35Z, `agt-96bec9` 19:55Z), both of which needed only 1-2 extra attempts and read
     "fluctuating-but-still-elevated, not resolved" rather than a climbing trend observed in real time. **No
     `features-service` code or workflow change made or needed** -- 4 different unrelated hang locations across 4
     identical-tree runs is conclusive against a code regression. Did NOT attempt a 5th manual retry: per this doc's own
     established posture (retrigger is the sanctioned resolution path, but shared CI-firefighter slot time is not
     unlimited, and load was rising, not easing, making a 5th attempt a poor-odds use of the same contended host).
     `main`'s `ci_status` will read `FAILING` (Firestore-recorded, confirmed via the run's own
     `Recording ci_status=FAILING for features-service` log line) until either a future manual re-verification during a
     calmer window, or the next `live-defi-rollout`->`main` promotion (334 commits still unpromoted at investigation
     time, so another promotion push -- and therefore a fresh `quality-gates-v2` attempt on a new commit -- is expected
     soon via the standing `ldr-to-main-promote-fleet.yml` automation) naturally re-verifies it. Flagging the
     climbing-load reading as fresh, real-time evidence for this doc's own still-open "revisit protected-6 self-hosted
     posture" question (last touched 2026-07-30 ~06:20Z with a NEGATIVE post-resize verdict) -- not re-opening that
     question myself, since it is already an explicit standing ask in this doc, not a new one. No code changed; slot
     left clean on `live-defi-rollout` (only this doc touched, via the PM plan-flip carve-out). Pinged
     `AUTHORING_SLOT=planning` with the outcome.
- **2026-07-30 ~23:20Z (cicd escalation `agt-df8b2b`, slot 5) — independent corroboration, same wall as `agt-5754dd`
  directly above (dispatched to a second slot concurrently)**: found `agt-5754dd`'s entry already covers this wall
  thoroughly (4 consecutive attempts, all 4 hanging at different unrelated locations) — not re-litigating the same
  finding in full. Two facts genuinely additive to their entry: (1) independently confirmed no-regression via diff scope
  from a different baseline pair — `git diff --stat` between the last-green main promotion (`9f3db938`, `20:39:50Z`) and
  the failing HEAD (`13a23d8e`) touches ONLY `calendar/` subsystem files, zero overlap with `delta_one/app/calculators/`
  or any of the 4 test files `agt-5754dd` saw hang; (2) while investigating, found slot 3 (`cicd` escalation
  `agt-a342eb`) concurrently mid-diagnosis of the LDR-side twin of this same wall — their progress message already
  confirmed a clean local `QG_SLICE=tests` run (17996 passed, 0 failed, 3m55s wall) and had re-triggered
  `live-defi-rollout`'s `quality-gates-v2` (run `30590084669`) for verification (`checks` leg green within ~5min;
  `tests` leg still running at investigation close). Did NOT start a 3rd/4th competing full `quality-gates.sh` run or CI
  re-trigger, matching `agt-5754dd`'s own stated posture — three concurrent escalations already converged on "host
  contention, no code fix" for the same wall; a further retry would only add load. **No code or workflow change made or
  needed.** Slot left clean on `live-defi-rollout`, only this doc touched.

- **2026-07-31 ~06:00-08:47Z (cicd escalation `agt-563fa4`, slot 3, `wall_type=main_ci_red`) — the dispatched wall WAS
  this doc's established pattern; a SEPARATE adjacent failure was NOT, and turned out to be a real bug, now fixed**:
  dispatched for `features-service` `quality-gates-v2` RED on `main` (commit `939f1967`, PR #913 "LDR → main (Option-B
  direct)"). Confirmed the promotion itself was not stuck (the PR's own qg-v2 run `30608398858` was green before merge);
  the post-merge push-triggered run on `main` (`30608403598`) died mid-`QG slice (tests)` inside
  `test_pubsub_subscriber.py` with exit 143 / "the runner has received a shutdown signal" — this doc's established
  signature. Re-ran the failed jobs once `glue-ip-172-31-5-118-1` was confirmed online+idle; went green (reconfirmed via
  `ci_status` at write-up time, `conclusion: success`, `blocked: false`).

  **Separately, `main-backmerge-to-ldr` failed on the same push (run `30608403128`) and 2 manual reruns — this was NOT
  this doc's host-contention class, despite superficially looking like one.** All 3 attempts died identically: ~0.7-0.8s
  after checkout, ZERO script output, empty `decision`/`reason` outputs on the downstream notify step, generic
  `exit code 1` — too consistent/deterministic across 3 attempts spanning 2h15m to be random contention (this doc's
  other entries show variable hang LOCATIONS and multi-minute durations; this was instant and identical every time).
  Reproduced locally with plain `bash -e` (not just reading the script): the `Promoted-From-LDR` trailer -detection
  loop's
  `_extracted="$(printf '%s' "$_msg" | grep -oE '^Promoted-From-LDR: [0-9a-f]{7,40}' | head -1 | awk '{print $2}')"`
  (template line 138) has no fallback for the — common, not edge-case — no-match result: under the script's own
  `set -o pipefail` + the step's `shell: bash -e {0}`, `grep` exiting 1 (no trailer on that candidate commit) propagates
  through the pipe as the bare assignment's exit status, and `-e` aborts the WHOLE SCRIPT immediately and silently,
  before any `echo` fires — exactly reproducing all 3 observed failures
  (`bash -e -c 'set -uo pipefail; _x="$(printf "%s" "no match" | grep -oE "nomatch" | head -1)"; echo "unreached"'`
  exits 1 with zero output). Most commits in a `live-defi-rollout..main` range won't carry the trailer (only
  squash-promotes do), so this triggers whenever a non-trailer commit happens to be OLDEST in the range — not rare.

  **Fixed + verified end-to-end, not just locally**: added `|| true` to the pipeline (comment explains why it's
  load-bearing) in the template SSOT (`unified-trading-pm@598aefd8` — bundled with an unrelated pre-existing
  `agent-rules-size-cap` fix below in the same push), then rolled out to the 2 repos whose live copies were confirmed
  actually broken — `features-service@ccd01cb8`, `agent-orchestrator@d43bbde` (the latter picked up only because
  `workflow-template-parity`'s ratchet gate flagged it as NEW drift once the template changed; it wasn't independently
  observed failing). Manually fired `workflow_dispatch` against `live-defi-rollout` post-fix (first attempt mistakenly
  targeted `main`, which doesn't have the fix yet — main only updates via the separate promotion cycle — and correctly
  re-failed on the old code, a methodology error not a fix failure): run `30617276725` succeeded, log shows
  `[backmerge] Promoted-From-LDR trailer found on 5e974169: using ce369620aa13 as explicit merge-base` →
  `explicit-base merge clean` → `DECISION: merged` — the loop now correctly walks past the no-match candidate instead of
  dying on it. This resolves the `main-backmerge-to-ldr` failures this doc's 2026-07-31 ~05:45Z entry flagged as "not
  diagnosed... flagging for whichever worker next touches features-service CI health" — that was me.

  **Also fixed, incidentally**: `cursor-configs/CLAUDE.md` was 83B over the 40,960B hard cap (`agent-rules-size-cap` QG
  check), blocking every PM commit's post-gate checks fleet-wide, not just mine — condensed 2 redundant clauses in the
  file's own maintenance preamble (`unified-trading-pm@598aefd8`, same push as the template fix), no meaning lost,
  40,900B after.

  **Deliberately NOT done**: the fleet-wide rollout of the backmerge fix to the ~22 other repos still carrying the same
  latent bug (`detect_template_drift.py --workflows` confirms) — scoped this escalation to the repos actually observed
  broken, to avoid piling more QG load onto the same contended host this doc tracks; tracked as a fresh `[SCRIPT] P2`
  todo above. Pinged `AUTHORING_SLOT=ci-reconcile` with the full outcome. All 3 touched repos (`features-service`,
  `unified-trading-pm`, `agent-orchestrator`) left clean on `live-defi-rollout`.

- **2026-07-31 13:39-16:22Z (slot 7, cicd, corroboration) — `unified-trading-system-ui`'s `glue-ip-172-31-5-118-1`
  runner, single-repo queue-depth measurement**: while re-verifying `registry-drift` for
  `ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` todo 3, shipped a fix
  (`unified-trading-system-ui@dfbfff68`) and watched its resulting `main` push CI run (`30635331302`) sit `queued`
  continuously for 2h43m+ (started 13:39:22Z, still queued at last check 16:22Z) with zero state change.
  `gh api .../actions/runners` showed the repo's one registered runner `busy: true` throughout, but
  `gh api .../actions/runs?status=in_progress` showed **zero** in-progress runs for this repo the whole time — i.e. the
  runner was tied up on ANOTHER repo's job, not this repo's own backlog, confirming cross-repo host contention rather
  than a stuck/dead runner. `gh run list --status queued` on this one repo showed **12 queued runs** spanning workflows
  (`CI - Test & Lint`, `Semver Agent`, `quality-gates-v2`, `Orphan Route Audit`, `Deploy UAT`, `main-backmerge-to-ldr`),
  oldest dated `2026-07-30T08:02:52Z` — i.e. a single-repo backlog that had NOT drained in over 30 hours at observation
  time. No new action taken (this doc's existing "accept recurring reds/delays, resolve via retrigger" posture already
  covers this — retriggering doesn't help a QUEUED-not-failed run anyway); flagging purely as a fresh, unusually
  sustained single-repo data point for whoever next re-evaluates the protected-6-stays-self-hosted posture. No code or
  workflow change made; only this doc touched.

- **2026-07-31 15:44-16:33Z (slot-6, data_engineering, corroboration) — `market-tick-data-service`'s
  `glue-ip-172-31-5-118-1` runner, same signature, blocking an `ldr-to-main-promote-fleet.yml` gate outright.** Shipped
  `market-tick-data-service@9ae23495` (a real correctness fix, unrelated to this crisis) and needed it to reach `main` +
  rebuild the deployed image before completing a live-verify. A direct `workflow_dispatch` of `quality-gates-v2` against
  LDR HEAD (run `30644139336`, created `15:44:02Z`) sat `status=pending` with **zero jobs ever created**
  (`gh run view --json jobs` → empty) for 49+ minutes straight — not a slow test run, the job was never even claimed.
  `gh api repos/.../actions/runners` shows exactly 1 runner (`glue-ip-172-31-5-118-1`), `busy: true` throughout, while
  `gh run list --status in_progress` shows **zero** in-progress runs for this repo the whole time (same cross-repo
  contention signature as slot-7's UI observation above) — plus a second, much older `queued` entry
  (`databaseId 26395100552`, created `2026-05-25`, workflow `workspace-qg`) still sitting in the same repo's queue,
  confirming genuinely-abandoned entries accumulate rather than eventually draining. Because this ISN'T just a slow/red
  check but the thing gating `ldr-to-main-promote-fleet.yml`'s decision to even OPEN a promote PR
  (`GATE BLOCK market-tick-data-service: ci_status=FAILING (cached='MAIN_GREEN', live='FAILING')`), no promote PR for
  this commit exists yet to regenerate/retry against — this doc's existing retrigger-doesn't-help posture applies
  identically. No workflow/infra change attempted (out of worker scope). Filed `/blocked` on my own task
  (`defi_venue_pipeline_to_live_ao_build-003`) recommending skip-and-resume-later rather than continuing to hold the
  slot; see that plan's Progress Log for the fix commit + resume point once this clears.

- **2026-07-31 ~15:17-15:26Z (review agent `agt-65ba48`, slot 1) — a THIRD `tmux_session_lost`-cluster signature this
  doc tracks: CPU-oversubscription, distinct from the IO/disk-full and RAM-exhaustion variants already logged above —
  formalizing (per main agent `agt-40d0ed`'s explicit disposition) a chat finding a prior review-agent session (this
  same persistent role) reported before itself being killed mid-conversation.** Independently re-verified via
  `GET /api/activity?type=tmux_session_lost&since=2026-07-31T15:00:00Z` (not relayed) — **THREE back-to-back kill waves
  in under 9 minutes, one more than main's own chat summary named**: **15:17:54Z** — slots 4, 8, 9, 12, 14 killed
  together (slot 9 released `prediction_satellite_ao_dispatch_batch4-023`, slot 8 released
  `tradfi_satellite_ao_dispatch_batch5-001`); **15:18:55Z** — slots 1, 5, 10 killed (slot 5 released
  `mdps_candle_manifest_near_total_coverage_gap-004`); **15:25:59Z** — slots 1, 4, 10, 12 killed (slot 4 released
  `ibkr_pipeline_mode_missing_venue_override-002`, slot 10 released `defi_satellite_ao_dispatch_batch3-015`, slot 12
  released `mtds_available_at_cross_asset_backfill-006`). That's **6 requeued tasks across all 3 waves** — the 15:17:54Z
  wave wasn't part of the original chat report to main; found it independently while pulling the raw event ids for this
  write-up (main's "4 requeued tasks" matches exactly the other two waves alone). Slot 1 (this review role's own slot)
  was killed repeatedly through the window — 15:18:55Z, 15:25:59Z, then again at 15:36:03Z, 15:40:08Z, and 15:48:41Z (5
  kills in ~30min).

  **New finding beyond the original chat report: the review role stayed down for ~2h15m after the last kill, not just
  slow to notice.** `GET /api/activity?slot=1&since=2026-07-31T15:45:00Z` shows the AutoSpawn respawn mechanism itself
  failing repeatedly after the 15:48:41Z kill: `spawn_retry_cap_reached` at **16:05:48Z** (retry_count=2,
  session_alive=false, pane_state="no_session") and again at **17:00:26Z** (same signature, session_alive=false) — two
  full retry cycles that never produced a live tmux session — before `agentkeeper_review_succeeded` finally landed at
  **18:04:03Z**, immediately followed by this session's own boot (`slot_boot` 18:04:44Z; the `boot_read_unconfirmed` 428
  the new `[DOCS] P3` todo above cites is this session's own 18:04:34Z rejection). Net: the review role — the fleet's
  only PR/discipline watcher — had **zero coverage for ~2h15m** (15:48:41Z→18:04:03Z), which is also the literal reason
  main's 15:38:12Z message sat unanswered until now. Working theory, not operator-confirmed: the same
  CPU-oversubscription this entry documents (load ~2x core count, 21 QG-related processes live) plausibly also made
  spawning a NEW tmux session + `claude` process unreliable on this host, i.e. the incident may have disabled its own
  oversight mechanism for the duration — consistent with, but not proven by, the timing (both failed-spawn attempts fall
  inside the elevated-load window; the eventual success at 18:04Z lines up with this entry's own fresh reading below
  showing load back down). Not opening a third todo for this unilaterally (main didn't ask for one and `does_not` on
  backlog-authoring applies) — flagging it to main via chat instead, for main to judge whether AutoSpawn's retry
  cap/backoff needs a longer allowance specifically for singleton roles (review/main) where a respawn failure means
  fleet-wide coverage drops to zero, vs. an ordinary worker slot where one task waits.

  **Root cause confirmed CPU-oversubscription, not IO/memory** — main agent `agt-40d0ed` corroborated on-host (same box,
  `ip-172-31-5-118`) at message time (2026-07-31T15:38:12Z): load 31.89 on 16 vCPU (~2x core count), memory fine (53Gi
  free — ruling out the RAM-exhaustion variant `orchestrator_vm_disk_io_contention_runner_burst_2026-07-28.md` tracks),
  but **13 concurrent `quality-gates.sh` + 8 concurrent `pytest` processes live** against the shared-host cap
  `max(2, floor(16/4))=4` — violated 3x+ on the QG count alone. Disposition (main, same message): same standing P1 root
  this doc's chain already tracks (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`, parent_epic
  `infrastructure_master`) — CPU-oversubscription is a NEW signature of that root, not a fresh incident; append here
  rather than file a new doc (784 lines at the time, well under the 1000 cap).

  **Current re-check (this write-up, 2026-07-31T18:08:44Z, ~2.5h after main's reading) — EASED, not worse**: load
  average now 6.00/6.85/7.17 (1/5/15-min) on 16 vCPU, comfortably under core count; `free -h` shows 29Gi free/45Gi
  available and swap 16Gi/47Gi used (still nonzero — consistent with this doc's standing
  "fluctuating-but-still-elevated" characterization, not "resolved"); QG-related process count back near cap — 3
  `quality-gates.sh` + 2 `pytest` = 5 vs cap 4, nowhere near the 21-process peak. Same "burst-not-sustained-worsening"
  pattern the 2026-07-30 16:39Z entry above established for that day's larger wave — not an ongoing crisis at write-up
  time. Two new todos opened above per main's disposition (`[BACKEND] P1` machine-enforced concurrency gate, `[DOCS] P3`
  boot-read-list gap). No code or infra change made this entry; read-only AO-activity-API + host `uptime`/`free`/`ps`
  queries only; slot 1 left clean on `live-defi-rollout` (only this doc touched).

- **2026-07-31 ~18:19-19:01Z (cicd escalation `agt-42e4c4`, slot 7, `features-service` PR#919, `ldr_qg_failure`)**:
  corroborating data point, no code fix warranted. The escalation context was a red `quality-gates-v2` on promotion PR
  #919 (13:31Z run `30634783434`) — by the time I picked it up the PR had already merged (13:31:24Z, `IggyIkenna`) and
  main's own post-merge gate had already gone green (`b5d7766c`), so nothing was actually blocked. Root-caused the
  original failure anyway before closing: the `tests` slice hit a `pytest-timeout` on
  `test_output_index_matches_input[1min-moving_averages]` (60s budget) and the `checks` slice separately hit
  `Type check FAILED/timeout (exit=124)` on the `typecheck` selector (`PYRIGHT_TIMEOUT:-120` in `base-service.sh`) —
  both selectors that only touch the same handful of feature calculators every run. Ruled out an actual code regression:
  locally profiled the flagged `MovingAverages` calculator on the identical synthetic fixture — `calculate()` completes
  in **1.4s**, nowhere near the 60s test budget. To get an independent confirmation I triggered a fresh
  `workflow_dispatch` of `quality-gates-v2` on `live-defi-rollout` HEAD (`97351fef`, a routine main→LDR backmerge with
  no manual diff) — it **also** failed, again on the `typecheck` selector, again at almost exactly the 120s mark
  (18:51:06.84Z→18:53:07.14Z = ~120.3s), while the immediately-following `lint-codex` slice's own basedpyright sanity
  check (STEP 5.21/5.22, same binary/cache) passed in ~15s. Two independent timeouts on content that was already proven
  clean (by profiling, by the prior LDR green at 16:35Z on the pre-backmerge commit, and by main's own green post-merge
  run) is the signature this doc already tracks, not a fresh regression. Host corroboration: `uptime` on
  `ip-172-31-5-118` (same box the CI runner `glue-ip-172-31-5-118-1` name resolves to) at 19:01:20Z read **load average
  15.14/14.26/14.74 on 16 vCPU** — climbed back up from the 18:08:44Z "eased" (6.00) reading two entries above, inside
  the ~45min window that contains my 18:50-18:53Z basedpyright timeout — consistent with this doc's
  "fluctuating-but-still-elevated," "burst-not-sustained-worsening" characterization, not a new incident. Disposition:
  no code change to `features-service`; did not force a third LDR retrigger (PR919 already resolved, nothing currently
  blocked, and per this doc's own "shared CI-firefighter slot time is not unlimited" guidance a periodic health-check
  re-run isn't worth spending more of it on). Appended here per the "protected-6 stay self-hosted, accept recurring
  reds, resolve via retrigger" posture rather than filing a new issue or a code fix. No repo state changed;
  `features-service` and `unified-trading-pm` slot-7 worktrees left clean on `live-defi-rollout` (only this doc
  touched).
