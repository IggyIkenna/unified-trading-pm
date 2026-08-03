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
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-29
last_updated: 2026-08-03
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
context_scope:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    agent-orchestrator/server/escalation.py,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]
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
      be compared side-by-side. **na-eligibility-audit 2026-08-01**: bounded, worker-determinable, conflict-check clear
      (no active/draft `assigned_vm: planning` doc in `parent_epic: infrastructure_master` already claims AWS Cost
      Explorer / EC2 instance-hours for this host) — a clean RECLASSIFY-eligible candidate, mirroring the sibling P1
      todo above it that was already done exactly this way. Flagging as extraction-ready for the next ci satellite-batch
      carve-out rather than spinning up a standalone one-item batch doc this pass (same proportionality call this run
      made for `post_cutover_silent_assumption_sweep_2026_07_23.md`'s F3 item) — doc stays NA in the meantime.
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
- [x] ✅ [BACKEND] P1. **New, opened by the 2026-07-31 ~15:17-15:26Z synchronized-multi-slot-kill corroboration below —
      main-agent-corroborated CPU-oversubscription, a distinct signature from the IO/disk-full and RAM-exhaustion
      variants already tracked.** Build a MACHINE-ENFORCED shared-host QG concurrency gate: a host-level
      `flock`/semaphore in `quality-gates.sh` (or `base-service.sh`) that blocks any run past `max(2, floor(cores/4))`
      concurrent full QG passes on one host — whether local AO-slot-worker QGs or self-hosted CI-runner QGs — so runs
      structurally cannot stack 13-deep the way they did at 2026-07-31~15:38Z (13 concurrent `quality-gates.sh` + 8
      `pytest` processes live, cap=4, violated 3x+ on the QG count alone — corroborated independently by both a
      review-agent session and main agent `agt-40d0ed` on-host). Self-discipline (the shared-host QG-sweep-batching rule
      in CLAUDE.md) is clearly not holding under load; this needs a structural block, not another documented violation.
      Done when: a concurrent QG run past the cap is measurably refused/queued (not just logged) on this host, verified
      by deliberately launching cap+1 QG passes and observing the (cap+1)th block until a slot frees. — **CLOSED
      2026-08-01 (na-eligibility-audit ci), tracking-vehicle redirect, not built standalone**: grepped
      `plans/active/*.md` for `flock`/`semaphore` and found
      `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` (status: active, assigned_vm: NA) already
      implements this exact mechanism more thoroughly — a flock-protected reservation-ledger admission governor (RAM
      two-clause gate + CPU gate + per-repo cgroup cap + FIFO fairness/aging), largely shipped, with only the
      live-admission cutover remaining (explicitly flagged there as "the safety-critical part... an operator-aware step,
      not an autonomous flip"). Building a second, independent flock/semaphore mechanism in the SAME scripts
      (`quality-gates.sh`/`base-service.sh`) risks a competing concurrency-control implementation. Redirecting this ask
      to that doc's tracking rather than re-implementing — see `qg_host_adaptive_resource_governor_2026_07_14.md` for
      the live cutover status.
- [x] ✅ [DOCS] P3. **New, opened by the same corroboration — a `boot_read_unconfirmed` gap hit firsthand this
      session.** `review.md`'s own "Boot — read the canonical files first" section names only `RULES.md` as the required
      pre-poll read; it never explicitly lists `worker.md`, yet the live `/api/slots/<N>/boot` endpoint's required-file
      check DOES enforce `worker.md` for the review role — confirmed directly: this session's own first `/boot` call was
      rejected 428 (`"missing": ["...agents/worker.md"]`) even after declaring `RULES.md` + `review.md` read
      (`GET /api/activity?slot=1` event `boot_read_unconfirmed` at 2026-07-31T18:04:34Z is this exact rejection). Add
      `worker.md` to the explicit required-pre-read list in both `review.md`'s boot section and `RULES.md` (wherever it
      enumerates per-role required reads), so a fresh review session's own docs tell it the true required set instead of
      discovering it via a 428 round-trip. Done when: `review.md` explicitly names `worker.md` as a required STEP-0/1
      read, and the documented set matches the server's actually-enforced set for role=review. — **DONE 2026-08-01
      (na-eligibility-audit ci)**: independently re-verified via a live `GET /api/activity?slot=1` query (225
      `boot_read_unconfirmed` events, 2026-07-27→2026-08-01, not just this doc's self-report) and by reading
      `server/prompts.py:expected_read_files` + `server/routes/slots_worker.py` directly (RULES.md has no per-role
      read-list to update — only `review.md` needed the fix). `agents/review.md`'s STEP 0 now explicitly lists
      `worker.md`. Filed `issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` for the residual
      live-incident follow-up (whether slot 1's CURRENT session self-recovers from a docs-only fix — an operator
      judgment call, not a worker-alone fix) — that doc, not this checkbox, tracks what's still open.

## Evidence

- Live query: `GET http://localhost:8765/api/escalations/active?include_resolved_within_hours=6` via SSM against
  `i-0c9b283b31d6b5ca7`, 2026-07-29T01:05:17Z and T01:08Z snapshots (raw JSON captured in this session's tool output,
  not reproduced here in full — re-run the same query for a fresh sample).
- Original doc: `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (1000 lines, at
  cap as of this writing).

## Progress Log

> **2026-08-03 line-cap remediation (round 2)**: this doc hit 999/1000 lines again (0 headroom for the context_scope
> backfill) — every entry dated 2026-08-02 ~19:30Z through the 2026-08-03 ~05:15Z entry was hoisted verbatim to
> `/plans/archive/2026_08/fleet_wide_qg_capacity_crisis_continues_day2_progress_log_history_2026_08_03.md` (mirrors the
> identical round-1 remediation this doc already got 2026-08-02, and its predecessor's own remediation 2026-07-29).
> Nothing below predates 2026-08-03 ~05:20Z.

- **context-scout 2026-08-03**: populated context_scope (5 entries).

- **2026-08-03 ~05:20-05:40Z (cicd escalation `agt-c77b30` re-dispatch, slot 4, `deployment-service`,
  `wall_type=ldr_qg_failure`, `pr_number=0`)** — same escalation id as the entry immediately above (slot 6's session
  ended before it resolved; re-dispatched). HEAD advanced one commit to `2349b67` (test-only `LC_TARBALL_FRESHNESS` pin
  in `test_vm_launcher_scripts.py`, unrelated). Independently reproduced the 3 `pytest-timeout` casualties from run
  `30782058442` directly — all 3 PASS in 34s. Ran full local `bash scripts/quality-gates.sh` at `2349b67`:
  **`✅ ALL QUALITY GATES PASSED (217s)`**, 3017 passed/5 skipped, sentinel written — 16th corroboration, 3rd
  independent local-green confirmation for this one escalation alone. No run was in-flight for this HEAD, so triggered
  one fresh `workflow_dispatch` per the established posture (`30787484781`). `GET /api/repo-blockers` → `open: []`
  (unrelated `features-service` entry only). No code/test change made or needed. Slot left clean on `live-defi-rollout`
  (only this doc touched).

- **2026-08-03 ~05:25-05:50Z (cicd escalation `agt-8e5d24`, slot 2, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`)** — the exact wall `agt-f70a66`/`agt-c82335`/`agt-15e651` (all above) diagnosed; per `agt-15e651`'s own
  note this should be the point a re-dispatch stops re-deriving the diagnosis and instead applies this doc's own
  established fix (the `PYTEST_TIMEOUT`-raise precedent in
  `pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md`), so that's what this session did. Confirmed the
  root cause unchanged: `main` still ~447 commits behind LDR, fleet-promote gate still
  `GATE BLOCK features-service: ci_status=FAILING`; LDR's own queued run `30780475199` had its `tests` leg genuinely
  claimed (not dead) but `checks` leg still unclaimed after 2.5h; failed run `30777261237` showed `pytest-timeout` on
  `test_momentum.py` (trivial 50-row df) + `Type check FAILED/timeout (exit=124)` — the same two catalogued signatures,
  no assertion failures. Host: `uptime` 37-42/16 vCPUs the whole session. Rather than a 5th no-op confirmation, applied
  the validated `unified-trading-api@71cdda0` mitigation pattern to this repo: `features-service@c092df50` adds
  `PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` AND `PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-300}` (this repo hits BOTH failure
  shapes, not just pytest) to `scripts/quality-gates.sh`. Verified locally: full `bash scripts/quality-gates.sh` at LDR
  HEAD `617388c5` (+ the uncommitted change) — **`✅ ALL QUALITY GATES PASSED (338s)`**, sentinel written, zero timeouts
  (17th corroboration). Shipped via `quickmerge --agent --files 'scripts/quality-gates.sh'`; first attempt died mid-run
  in the (non-blocking, CI-irrelevant — `QG_SLICE`-scoped CI runs never reach this loop) peripheral-dir advisory loop
  after a peer's push invalidated the sentinel and forced a Pass-2 re-gate, same host-pressure signature as the core
  failure this doc tracks; retried and the sentinel-verified fast-path landed clean second time
  (`✅ Landed on live-defi-rollout`), confirmed via `merge-base --is-ancestor` on origin. Also fast-pathed repo-blocker
  `RB-417918ff` (a genuinely separate, already-fixed-by-another-slot bug — `617388c5`'s `_verify_test_manifest` 4→3-arg
  signature update, confirmed passing in this session's local run) via `POST /api/repo-blockers/RB-417918ff/resolve` (2
  waiters notified). `AUTHORING_SLOT=ci-reconcile` not a live numeric slot — same non-int rejection as prior entries;
  this doc entry is the outcome record. Did not manually retrigger LDR's own in-flight `quality-gates-v2` run — both
  legs were genuinely progressing, a duplicate dispatch would only add load. **Next occurrence for this repo should
  observe whether the timeout raise actually clears it** (mirrors
  `pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` todo 1) before repeating either the no-op
  confirmation OR another timeout raise. Slot left clean on `live-defi-rollout` (only `features-service` touched by this
  session's code commit + this doc).
