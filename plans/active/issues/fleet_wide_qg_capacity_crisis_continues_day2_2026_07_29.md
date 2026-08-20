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
author: unknown
last_updated: 2026-08-20
priority: P1
parent_epic: ci_master
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
- [x] ✅ [DEVOPS] P3. **RESOLVED 2026-08-08 — root access confirmed working; ran the check live; result is NOT what the
      working hypothesis assumed.** Operator believed root access may have already been granted — re-tested live via
      `aws ssm send-command` (`AWS-RunShellScript` document) against `i-0c9b283b31d6b5ca7`: **`whoami` returns `root`**
      — SSM Session Manager's `RunShellScript` runs as root on this instance, confirmed working right now, no further
      grant needed. Went to pull `dmesg`/`journalctl -k` directly: the instance **rebooted 2026-08-07T10:40:44Z** (new
      kernel `7.0.0-1010-aws`, up from `6.17.0-1019-aws`) — both `dmesg`'s ring buffer and journald's live boot ID
      (`journalctl --list-boots` shows exactly one boot, starting 2026-08-07T16:46:29Z) only cover since that reboot, so
      neither can see 2026-07-30 directly. **Found the data anyway** in the ROTATED classic syslog (not journald) —
      `/var/log/kern.log.1` (rotated 2026-08-01T23:59, so its content spans 2026-07-26 through 2026-08-01, covering the
      incident) is intact and has real content for that day (809 log lines dated `2026-07-30`, verified via
      `awk -F"T" '{print $1}' | sort | uniq -c`). **Grepped the exact incident window** (`2026-07-30T14:` +
      `2026-07-30T15:` timestamps) for `oom|out of memory|killed process|invoked oom-killer` (case-insensitive): **ZERO
      matches** — confirmed twice, once windowed to the 14-15Z hours and once for the ENTIRE day 2026-07-30 (also zero).
      Read the actual full kernel-log content for the 14:00-16:00Z window directly (not just grep counts): every single
      entry in that 2-hour span is a routine, ~5-minutes-apart
      `cgroup: fork rejected by pids controller in /system.slice/<audit-stale-gate-references|process-category-sampler|audit-false-done>.service`
      — a PID-limit rejection on three specific MONITORING/audit systemd services, not memory pressure, and not touching
      any AO worker/tmux cgroup. Also checked `/var/log/syslog.1` for `systemd-oomd`/`memory.pressure` activity in the
      same window — zero matches there too. **Verdict: the kernel OOM-killer was NOT invoked during the 2026-07-30
      14:54-15:01Z window** — this doc's own working hypothesis ("swap 14-16Gi used + load peak ~26/16vCPU are
      consistent with memory pressure") is NOT supported by the kernel log; the log-confirmable mechanism this todo
      asked for is a clean NO, not a confirmation. **This closes the todo as asked** (get the actual finding and close
      it for real) — the mass `tmux_session_lost` cluster's real cause is NOT a kernel OOM kill and needs a fresh,
      differently-scoped investigation (new todo below); do not re-open this exact question, it is answered. **Method
      note for future root-access sessions on this host**:
      `aws ssm send-command --instance-ids i-0c9b283b31d6b5ca7 --document-name AWS-RunShellScript --parameters 'commands=["<cmd>"]'`
      then `aws ssm get-command-invocation --command-id <id> --instance-id i-0c9b283b31d6b5ca7` — no interactive
      session, no operator grant needed, works today with the credentials already in this workspace.
- [x] ✅ [DEVOPS] P3. **NEW 2026-08-08 — find the REAL cause of the 2026-07-30 14:54-15:01Z mass `tmux_session_lost`
      cluster** (slots 1, 4, 5, 9, 10, 11 killed across 3 waves in ~7 min), now that the OOM-killer hypothesis above is
      RULED OUT by direct kernel-log evidence. Candidates worth checking first, none yet investigated: (a) a
      cgroup/systemd unit restart or resource-limit action outside the kernel's own OOM path (e.g. an AO watchdog or the
      `process-category-sampler`/`audit-*` services seen firing every ~5min in that exact window — check whether any of
      THOSE three services' own actions, not memory pressure, coincide with the 3 kill waves); (b) a manual or scripted
      `tmux kill-session`/process-manager action around that timestamp (check AO's own dispatch/respawn logs, not just
      the host kernel log); (c) an AWS-side event (spot interruption warning, instance status check, EBS throttling) via
      `aws cloudwatch`/`aws ec2 describe-instance-status` for that exact window (data still available — CloudWatch
      retention is much longer than a syslog rotation). Root access is now confirmed working (see the resolved todo
      above) — this is directly investigable, not blocked. **DONE 2026-08-14 (slot 6, infra) — CLOSES with a verdict:
      candidate (a), system-wide thread/PID (not memory) exhaustion. (b) and (c) directly ruled out by evidence; full
      timeline + log excerpts in the Progress Log entry below.**
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
- [x] ✅ [BACKEND] P2. **New 2026-08-03 (main agt-1756f6, via review agt-07ff49 msg #3566).** Ship the stranded,
      diagnosed-good features-service fix `030c8b95` (`fix(ci): raise PYRIGHT_TIMEOUT 300s→600s` — 300s still timing out
      under fleet QG contention; slot-4 authored 2026-08-03 16:48Z, then went diverged; the unpushed-commits watchdog
      preserved it to `origin/wip-preserve/slot-4-features-service-diverged-20260803T171854Z`). Slots 2/4/9
      independently re-diagnosed this SAME PYRIGHT_TIMEOUT contention today — ship it forward rather than let a 6th slot
      re-diagnose from scratch: rebase the wip-preserve ref onto current `origin/live-defi-rollout`, run
      features-service QG green, ship via quickmerge. Same root wall_type as this doc's capacity crisis. Repo:
      features-service. Done when: `030c8b95`'s timeout bump is an ancestor of `origin/live-defi-rollout` (QG-verified).
      **RESOLVED 2026-08-08 (`ci_satellite_ao_dispatch_batch6` todo 2) — superseded, not shipped verbatim.** Attempted
      the rebase: `git rebase origin/live-defi-rollout` onto
      `origin/wip-preserve/slot-4-features-service-diverged-20260803T171854Z` conflicts on `scripts/quality-gates.sh` —
      every OTHER commit on the stranded branch (`52a7de5c`, `0f894013`, `87942ac0`, `3b0c0b05`) is already an ancestor
      of LDR (landed independently since 2026-08-03), and `030c8b95`'s own substance
      (`PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-600}`) is ALREADY live on LDR via a separately-authored commit,
      `features-service@7c86a6b1` (2026-08-06, same slot-4 author, same 300s→600s content, different comment/SHA — one
      of the "Slots 2/4/9 independently re-diagnosed" instances this todo's own text anticipated). The conflict is
      value-identical (both sides set 600s), confirming there is nothing left to ship — rebasing `030c8b95` forward
      would only reintroduce a stale comment. Verified: `PYRIGHT_TIMEOUT=${PYRIGHT_TIMEOUT:-600}` present at
      `features-service/scripts/quality-gates.sh:46` on `origin/live-defi-rollout` HEAD (`3384ea29`);
      `git merge-base --is-ancestor 7c86a6b1 origin/live-defi-rollout` → true. No commit needed; local scratch branch
      `_stranded_pyright_fix` used for the rebase attempt was discarded (never pushed).
- [x] ✅ [SCRIPT] P2. **New, opened by the `main-backmerge-to-ldr` pipefail+`-e` root-cause fix below.** The template
      SSOT (`unified-trading-pm@598aefd8`) and 2 repos' live copies (`features-service@ccd01cb8`,
      `agent-orchestrator@d43bbde`) are fixed, but `detect_template_drift.py --workflows` shows this template has 28
      baselined/grandfathered-drift + more not-yet-diverged copies across the ~25-repo fleet — every repo still on the
      OLD copy carries the SAME latent bug (silently dies, zero output, whenever the oldest commit in a
      `live-defi-rollout..main` range lacks a `Promoted-From-LDR:` trailer — not rare, any non-squash-promote commit mix
      triggers it). Run the fleet-wide rollout
      (`bash scripts/workflow-templates/rollout-workflow-templates.sh --template main-backmerge-to-ldr.yml`, no `--repo`
      filter) + a quickmerge per touched repo, once host capacity allows (this session deliberately scoped to only the 2
      repos actively observed broken, to avoid piling more QG load onto the same contended box this doc tracks). Done
      when: `detect_template_drift.py --workflows` shows 0 copies still carrying the pre-fix content for this template.
      **DONE 2026-07-31 (slot 4, cicd)** — a dry-run against the actual auto-rollout target set (not the todo's assumed
      ~25) found only 5 repos genuinely still on pre-fix content (`system-integration-tests@2d35879`,
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

- **2026-08-03 ~21:32Z (review agt msg #3596, main agt-1756f6 verified on-host)** — fresh CPU-oversubscription incident,
  the strongest QG-count reading yet on this box. Review reported ~18 concurrent `quality-gates.sh` + loadavg 31.5; main
  re-measured live seconds later and found it **WORSE — 26 concurrent `quality-gates.sh` on 16 cores** (cap=4, violated
  6x+ on the QG count alone), loadavg **33.49 / 29.69 / 28.39** (>2x oversubscribed). Concrete harm this time is a real
  ship failure, not just elevated load: **slot 2 (task `mtds_type_ignore_ratchet_regression`, repo
  market-tick-data-service) reported 3 consecutive ship attempts dying ~7min in at 68% test progress, self-diagnosed as
  host contention (not a code defect) and backed off.** Review flags a likely compounding factor: 8+ `ldr_qg_failure`
  cicd-escalation agents spawned across repos in the prior ~45min, each running its own QG investigation on top of
  normal worker QG load — so some red-gate signals may themselves be contention-induced flakiness rather than real
  regressions (echoes the 16th-corroboration local-green pattern logged above). Worker-level backoff (slot 2) is the
  ONLY mitigation live and is reactive/uncoordinated, so runs will pile back up. **This is fresh, concrete justifying
  harm for the still-pending fix**: the machine-enforced host QG concurrency gate is already built in
  `/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` (flock-protected reservation-ledger admission
  governor, largely shipped) — the ONE remaining piece is the **live-admission cutover**, explicitly flagged there as
  the safety-critical, operator-aware step (not an autonomous flip). Today's slot-2 ship failures are exactly the harm
  that cutover prevents; surfacing to the operator as justification to prioritize it. Main took no process-kill action
  (bulk-killing another slot's in-flight QG/pytest is BANNED per CLAUDE.md multi-agent-safety; these are legitimate
  runs, not a single runaway). Separately noted by review (FYI, already self-healed, no action): a mass
  `tmux_session_lost` sweep at 21:23:17Z across slots 1/4/5/8/12 + a ~90s orchestrator restart ~21:30Z — all recovered
  via existing AutoSpawn/inherit-dirty-WIP, no data loss.

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

- **2026-08-03 ~12:35-12:52Z (cicd escalation `agt-a45acf`, slot 2, `market-data-processing-service`,
  `wall_type=ldr_qg_failure`, `pr_number=0`)** — 6th cicd dispatch onto this exact repo/wall today (after `agt-68298f`,
  `agt-dbfcd7`, `agt-2c266f`, `agt-6db91d`, `agt-895b89`, all above, all "no code/test change made or needed"). Run
  `30809754899` (11:29:42Z, 1h5m53s) confirmed the identical catalogued signature: `QG slice (tests)` progressed to 77%
  then went silent 7min before `PluggyTeardownRaisedWarning`/`OSError: cannot send (already closed?)` during
  `pytest_sessionfinish`, `exit=1` — zero genuine `FAILED tests/...` lines. Host at investigation time: `uptime` load
  average **20.14/22.22/23.56** (16 vCPUs, still >1.25-1.5x oversubscribed), swap **18Gi/47Gi** in use, 16 concurrent
  `quality-gates.sh` processes, 11 `Runner.Worker` processes — same contention class, somewhat lower than the ~04:11Z
  entry's 42.03 peak but not cleared. Per `agt-8e5d24`'s own "next occurrence should apply the fix rather than another
  no-op" directive (this repo's 6th dispatch, well past that bar) and MDPS not yet carrying the mitigation (checked
  `scripts/quality-gates.sh` — only a separate `MDPS_PERF_TEST_TIMEOUT_SECONDS` override existed for the unrelated perf
  gate, nothing for the main pytest slice's `PYTEST_TIMEOUT`), applied the same proven pattern as
  `unified-trading-api@71cdda0`/`features-service@c092df50`: `market-data-processing-service@42d4c1f` adds
  `PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` to `scripts/quality-gates.sh` (confirmed this repo sources `base-service.sh`,
  the `PYTEST_TIMEOUT`-keyed copy of the PARGS line, not `base-library.sh`'s `PYTEST_TIMEOUT_SECONDS` — right variable
  name verified before editing, not assumed from the other repos' diffs). Verified locally: full
  `bash scripts/quality-gates.sh` (backgrounded per the mandatory pattern) at LDR HEAD `1c8588c` + the change —
  **`✅ ALL QUALITY GATES PASSED (80s)`**, tests leg `2332 passed, 2 skipped, 27.59s`, zero timeouts (18th corroboration
  this doc-pair has accumulated of "local green, CI red = pure contention"). Shipped clean first attempt via
  `quickmerge --agent --files 'scripts/quality-gates.sh'` (`✅ Landed on live-defi-rollout`), confirmed via
  `merge-base --is-ancestor 8fa00db origin/live-defi-rollout`. `GET /api/repo-blockers` → `open: []`, nothing to
  fast-path. No run was in-flight for the new HEAD, so triggered one fresh `workflow_dispatch` (`30815224742`) and did
  NOT hold the slot waiting on it — per this same doc-pair's own prior direct guidance to this slot (a queued message
  from an earlier session on this exact wall class: "holding a slot for hours while it crawls is precisely the
  over-watch anti-pattern... repo-health-watcher polling for the eventual green"), a locally-verified green plus one
  clean retrigger is the disposition, not a held wait. `AUTHORING_SLOT=ci-reconcile` not a live numeric slot — same
  non-int rejection as every prior entry; this doc entry is the outcome record. **Next occurrence for THIS repo should
  observe whether the raise actually clears CI** (mirrors `agt-8e5d24`'s own open question for features-service) before
  repeating either a no-op confirmation or another timeout raise. Slot left clean on `live-defi-rollout` (only
  `market-data-processing-service` touched by this session's code commit + this doc).

- **2026-08-03 ~18:19-18:45Z (cicd escalation `agt-f91096`, slot 7, `ml-service`, `wall_type=ldr_qg_failure`,
  `pr_number=335`)** — dispatched against a promotion PR (`ml-service#335`, LDR→main, real code diff:
  `scripts/ml_orphan_sweep.py` + its test, not a chore/version-only promote). By dispatch time the PR had **already
  merged** (`merged_at=2026-08-03T17:16:15Z`, 3s before the failing check `30835989289` even started) — nothing was
  actually blocked. Diagnosed the failing run: `checks` job's `typecheck` slice waited **880s** in the QG-governor's
  `WAIT_CPU` admission queue before being reserved, then hit the hard **120s basedpyright timeout** (`exit=124`,
  `ERROR_COUNT=0`/`WARN_COUNT=0` — never got far enough to emit any real type-error output), consistent with this
  doc-pair's catalogued "local green, CI red = pure contention" signature, not a code break. Host at investigation time:
  `uptime` load average **42.38/39.82/35.15** (16 vCPUs, ~2.6x oversubscribed), swap 18Gi/47Gi in use, one LDR
  `workflow_dispatch` run queued 45+min without even starting, another `main`-push run (`30838328689`, post this
  promotion) also queued 45+min at time of writing — same root cause
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` (Phase 1 shipped this same day, Phase 2/3
  live-validation + fleet rollout still pending) and `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`
  (canary-only migrated so far; ml-service still on the old oversubscribed box) are both actively fixing. Ran a scoped
  local repro (`QG_SLICE=typecheck`, backgrounded, heartbeated) at the same `live-defi-rollout` HEAD (already carries PR
  335's diff): **`✅ QG_SLICE=typecheck PASSED`** — 223 pre-existing basedpyright errors reported but non-blocking
  (ml-service has no `BASEDPYRIGHT_MAX_ERRORS` ceiling set, a pre-existing repo-config gap unrelated to this wall, not
  touched here), 0 new blocking issues — confirms no code regression, 19th corroboration this doc-pair has accumulated
  of the pure-contention signature. No code/test change made or needed (PR already merged; local repro clean).
  `GET /api/repo-blockers` → `open: []`, nothing to fast-path. Did not force a duplicate re-trigger — a fresh
  `main`-push `quality-gates-v2` run (`30838328689`) was already queued for this exact HEAD+successor commit; adding
  another dispatch would only add load to the same saturated queue, mirrors this doc-pair's own established "did not
  hold the slot waiting on it" disposition. `AUTHORING_SLOT=ci` not a live numeric slot — same non-int skip as every
  prior entry (cicd.md's regex-gated ping step); this doc entry is the outcome record. Slot left clean on
  `live-defi-rollout` (only this doc touched).

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, valid (mixed reasons per item),
re-read end-to-end (doc grew substantially today via the entries above since the last marker). 3 open todos: (1) AWS
Cost Explorer $ quantification for the retry storm — this doc's own 2026-08-01 audit note already called this
RECLASSIFY-eligible but deliberately deferred extraction; re-confirmed still deferred by BOTH
`ci_satellite_ao_dispatch_batch4_2026_07_31.md` and `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (D5-6: "Same
precedent batch3 and batch4 both applied: do not fold an actively-evolving incident doc's items into a static batch.
Re-triage once its own Progress Log shows the capacity question settled") — doc is still actively evolving (grew again
today), so respecting the standing deferral rather than proposing a fresh RECLASSIFY. (2) OOM-killer `dmesg`/
`journalctl -k` confirmation — needs root, operator-gated. (3) `RETRY_PER_TICK` scaling design question — genuine
undecided tradeoff, "leave as-is" is a valid outcome. No RECLASSIFY, no ARCHIVE. Flagging item 1 for whoever next
assembles a ci satellite batch once this doc's Progress Log stabilizes.

- **2026-08-03 ~19:56Z (main agt-1756f6, via review agt slot-1 flag msg #3584)**: Fresh confirmed incident instance of
  the runner-pool starvation — verified LIVE via GitHub API: `quality-gates-v2` runs stuck in `queued` (never starting,
  NOT failing) on market-data-processing-service (oldest 81min), deployment-service (25min + two at 55min),
  instruments-service and unified-api-contracts (~25min), WHILE greeks-service + execution-service completed SUCCESS
  normally in the same window. The subset pattern (queued-never-starts on some repos, clean completion on others) is the
  self-hosted-runner-POOL starvation signature — greeks/exec hit a healthy pool. This is what's driving the recurring "N
  tasks blocked on prereqs" idle-slot state (slots 4/9/12) and it lines up with the escalation_unresolved pings already
  firing (some reescalated=true) on exactly these repos. `/api/repo-blockers` was empty — that §4b filing is
  worker-owned (a worker files when its task is CI-blocked), main does not file it. Root fix = runner capacity
  (operator/infra), already this doc's open remediation. Recorded here so the next incarnation inherits the datapoint
  instead of re-discovering it.

- **2026-08-03 ~20:30Z (interactive session, `/autonomous` on
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md`) — material improvement, NOT full resolution.** One of
  this crisis's root causes — the reservation-ledger governor resolving a SEPARATE, isolated ledger per repo on this
  same shared host (confirmed 2026-08-02, ~10 repos piling on with zero shared admission) — is now fixed and live:
  `unified-trading-pm@fada7dc20` extends `_qg_shared_root()` to collapse every glue-runner pool's ledger onto one
  shared, host-writable path (`/opt/.qg-governor-glue-shared`), propagating organically to every pool via its next CI
  run (no fleet "flip" step). Live-validated via direct host introspection (not just synthetic test): **before** — 10
  repos, each blind to the other 9's reservations, admitting as if it owned the whole host; **after** — 6+ real
  concurrent repos (`client-reporting-api`, `deployment-service`/`-api`, `batch-live-reconciliation-service`,
  `instruments-service`, `features-service`, `unified-api-contracts`, seen across 3 separate spot-checks this session)
  correctly sharing one ledger, admission math (`running heavy phases` vs `CPU slots (80%×N)`) actually binding, 0 OOM
  observed. **What this does NOT fix** — the `~19:56Z` entry immediately above this one is a DIFFERENT root cause this
  fix doesn't touch: runner-POOL starvation (a pool with zero available runner processes queues forever, never even
  starting — a capacity/count problem, not an admission-coordination one; this doc's own remediation for that is
  runner-count policy, separate from the ledger fix). Also out of scope: AO slot-worker QG runs (a separate
  `.tabs`-scoped ledger population on this same host) are still NOT unified with the glue-runner pools' ledger — two
  populations sharing a host but not yet a combined budget view. Neither this doc nor
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (at 995/1000 lines — no new entry added there, see
  that doc's own note on why continuations land here) should be marked resolved on this fix alone. A ~90min live soak of
  the ledger fix specifically is running in the background at time of writing; see
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md`'s Progress Log for its outcome.

- **2026-08-03 ~21:20Z (cicd agent slot-5, escalation `agt-31303a`, wall_type=ldr_qg_failure, strategy-service#485)** —
  same signature, same repo, third corroboration this week (see the `~15:40Z 2026-08-02` entry above, `agt-6f553d`).
  Dispatched on `quality-gates-v2` FAILURE, run
  [30843816625](https://github.com/IggyIkenna/strategy-service/actions/runs/30843816625): job-level breakdown shows
  `QG slice (tests)` SUCCESS (19:01:45→19:12:10) but `QG slice (checks)` FAILURE — its own log shows the `qg-governor`
  CPU-admission wait alone ran 1526s (~25.4min, `WAIT_CPU 30s`→`WAIT_CPU 1500s` ticks) before basedpyright even started,
  then basedpyright hit the documented hard `Type check FAILED/timeout (exit=124)` at exactly 120s (`PYRIGHT_TIMEOUT`
  default) with 0 errors/0 warnings extracted — the canonical host-contention-timeout signature this doc tracks, not a
  code regression. Confirmed via live host check: `uptime` load average 30.80/29.54/28.96 on the same implicated box,
  consistent with the crisis still being active. Did NOT need a local repro or code fix — PR #485 was **already
  `MERGED`** (`mergedAt=2026-08-03T19:00:21Z`) by the time this escalation was triaged: the actual `push:main`
  `quality-gates-v2` run for the merge commit
  ([30843825878](https://github.com/IggyIkenna/strategy-service/actions/runs/30843825878)) ran independently and
  completed SUCCESS (29m11s), and `live-defi-rollout`'s own latest `quality-gates-v2` `workflow_dispatch` run is green
  (36s, content-sentinel hit). `gh pr list --state open` → `[]`, `/api/repo-blockers` → no `strategy-service` entries —
  nothing is currently blocked. Same "merged via an already-satisfied required-check path independent of this specific
  run" pattern as every prior corroboration in this doc. No code/test/workflow change made or needed; did not touch
  `self_hosted_runner_labels` (`strategy-service` stays on the operator's protected-6, per the 2026-07-28 ruling).
  `$AUTHORING_SLOT` was the literal sentinel `ci` (not a numbered slot) — skipped the authoring-slot ping per
  `cicd.md`'s rule (no real originator to notify; the dispatch-time Slack alert already covered the FYI). Slot left
  clean on `live-defi-rollout` (only this doc touched).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — evolving incident log, OPERATOR OOM-dmesg, design tradeoff

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:8d49128a486bd493]: KEEP-NA,
valid — 3 open items re-verified end-to-end. The RETRY_PER_TICK design-tradeoff item (line 231) blocks whole-doc
RECLASSIFY on its own (genuine open tradeoff, "leave as-is" explicitly valid). Flagging the other 2 as
`MISCLASSIFIED_LIKELY_AO_ELIGIBLE` for a closer look next round: the AWS Cost Explorer $ quantification item (line 176)
has been marked "extraction-ready" since 2026-08-01 but never actually extracted across 7+ subsequent batches —
re-verify the conflict-check is still clear and consider a satellite-batch pull rather than another citation-only
confirm; the tmux_session_lost root-cause investigation (line 220, filed 2026-08-08) has concrete candidate steps
(a/b/c) and may be bounded enough for extraction, though it concerns a now 10-day-stale incident. Neither promoted to
RECLASSIFY this run (doc-level flip blocked by item 3; sub-item extraction is `/ag-closeout-audit`'s satellite-batch
mechanism, not this skill's). No `assigned_vm` change.

- **2026-08-14 (slot 6, infra) — REAL CAUSE of the 2026-07-30 14:54-15:01Z mass `tmux_session_lost` cluster found:
  candidate (a), system-wide thread/PID exhaustion (a resource-limit failure DISTINCT from the kernel OOM-killer already
  ruled out above). (b) manual/scripted kill and (c) AWS-side event both directly ruled out by evidence. This session
  ran DIRECTLY on `i-0c9b283b31d6b5ca7` itself (a slot worker's `.tabs/6` checkout lives on this same shared host) — no
  SSM needed; `adm`-group membership gave direct read access to the rotated host logs
  (`/var/log/{kern,syslog,auth}.log.2.gz`, the rotation covering 2026-07-26→08-02) plus the local `agent-orchestrator`
  checkout's own uvicorn stdout→syslog stream.** **(c) ruled out**: `aws ec2 describe-instances` shows
  `InstanceLifecycle: null` (on-demand, not spot — spot interruption is categorically impossible) and
  `LaunchTime: 2026-08-09` (a LATER stop/start, not relevant to Jul 30). `aws cloudtrail lookup-events` for
  `ResourceName=i-0c9b283b31d6b5ca7` across 2026-07-29→08-14 shows NO `StopInstances`/`RebootInstances`/`StartInstances`
  anywhere near the window (nearest pair: 2026-07-29 04:43-04:47Z, ~34h earlier; next after that: 2026-08-07).
  `aws cloudwatch get-metric-statistics --metric-name StatusCheckFailed` reads `Maximum: 0.0` for every 5-min datapoint
  across 13:00-17:00Z. No AWS-side event touched this instance in the window. **(b) ruled out**: `zgrep` of
  `/var/log/auth.log.2.gz` for the exact 14:52-14:57Z window (and the wider 14:45-15:05Z) shows zero
  `kill`/`pkill`/`tmux`-containing sudo `COMMAND=` entries — only routine cron-driven `git config gc.pruneExpire never`
  / `git fsck --connectivity-only` maintenance from `slot-cron-ff-pull.sh`-family scripts. No human or script issued a
  kill/tmux-kill/systemctl-stop command in or around the incident window. **(a) confirmed — system-wide thread/PID
  exhaustion, not memory**: `zgrep` of `/var/log/kern.log.2.gz` for the full 14:00-16:00Z window (re-confirming the
  already-closed OOM todo above) shows every kernel line in that span is the routine
  `cgroup: fork rejected by pids controller in /system.slice/<audit-stale-gate-references| process-category-sampler|audit-false-done>.service`
  pattern — scoped to those 3 services' own cgroups, not the orchestrator/tmux cgroup, so not a direct kill mechanism on
  its own. But a SEPARATE, broader signal brackets the exact incident window: `RuntimeError: can't start new thread`
  (Python `threading.Thread.start()` failing at the OS level — `pthread_create` returning EAGAIN, i.e. a
  **process/thread-count** ceiling, not RAM) fires repeatedly at 14:46:32Z, 14:52:07Z, and 14:56:27Z — i.e. immediately
  before, and squarely inside, the reported 14:54-15:01Z window. In the SAME stretch the production orchestrator server
  itself (port 8765, real dashboard/API traffic from real operator IPs) was caught in an externally-triggered restart
  storm: 10 distinct fresh process starts between 14:47:23Z and 14:49:53Z (each logging the full `Ready on UTC ...` boot
  sequence, some then logging `Shutting down` within **milliseconds** of `Application startup complete` — i.e. a clean
  external SIGTERM arriving instantly, not an internal crash/traceback). `KillMode=process` on `orchestrator.service` (a
  deliberate 2026-05-20 fix, confirmed still live in the unit file) means these restarts do NOT directly kill spawned
  tmux worker sessions — cross-checked and ruled out as the direct mechanism. The restart storm's own trigger is
  `scripts/ao-self-pull.sh`'s stale-process self-heal: its dedicated log (`/var/log/ao-self-pull.log`, not syslog)
  shows, at the 14:45:01Z cron tick immediately preceding the storm:
  `current (8809ee3) but running process predates HEAD ... restarting stale process` →
  `orchestrator restarted (active=active)` → immediately followed by
  `WEDGE (running process stuck 4 consecutive ticks behind HEAD (stale-process self-heal not resolving)) — no webhook` —
  i.e. the self-heal had ALREADY been failing to converge for 4 consecutive 15-min ticks (~1h) before this entry,
  consistent with a host too thread/PID-starved for a freshly restarted process to fully stabilize before the next
  check. The production process only truly stabilized at 14:49:53Z (PID 1510252, which then ran continuously) —
  TmuxPruner (the in-process daemon that DETECTS, not causes, vanished sessions) logged its first post-stabilization
  staleness finds at 14:54:09Z (`cleared 5 stale tmux_session reference(s)`) and 14:56:11Z
  (`cleared 1 stale tmux_session reference(s)`) — 6 total, matching the 6 reported slots (1, 4, 5, 9, 10, 11) — squarely
  inside the 14:56:27Z thread-exhaustion recurrence. **Verdict**: the same system-wide thread/process-count exhaustion
  that (i) crashed `process-category-sampler` with `can't start new thread`, (ii) wedged the orchestrator's own
  restart-self-heal for an hour, and (iii) rejected forks in 3 unrelated monitoring-service cgroups, most plausibly also
  hit the affected slots' own `claude`/tmux client process trees directly — a Node.js/Python process attempting to spawn
  a thread or fork a subprocess under this same ceiling fails/dies at the OS level, which is exactly the "resource-limit
  action outside the kernel's own OOM path" this todo's own candidate (a) named, just not the specific
  `process-category-sampler` cgroup mechanism originally guessed — a HOST-WIDE `nproc`/`threads-max` ceiling under 13-20
  concurrent AO slot-worker sessions + up to 22 self-hosted CI runner pools on one 16-vCPU box, not a per-service cgroup
  limit. No further host-level forensic evidence survives to pin the exact numeric ceiling hit (this rotation is the
  last one with 2026-07-30 coverage; `/var/log/orch-watchdog/` snapshots — which would have shown live `tmux ls` +
  `pgrep -af claude` + `/proc/sys/kernel/threads-max` at the moment — are long past their 12h/720-snapshot retention).
  This closes the todo's own question; a follow-up (raising `DefaultLimitNPROC`/`kernel.threads-max` headroom, or the QG
  host adaptive resource governor's live-admission cutover already tracked in
  `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`) is a distinct, already-tracked mitigation, not
  reopened here.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:c1657352b96324ef]: KEEP-NA,
valid — MANDATORY RE-ASSESSMENT of the 2 carried-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE items from the 2026-08-09 run,
completed. Item 3 (line 231, RETRY_PER_TICK global-vs-partitioned retry-budget tradeoff in server/escalation.py)
RE-CONFIRMED as a genuine open design tradeoff that blocks whole-doc RECLASSIFY on its own: its own 'Done when' clause
offers 2 non-mechanical paths -- (a) a recorded 'leave as-is' ruling, or (b) ship+verify a scaled/partitioned budget
against a live comparable incident burst -- neither is a single checkable fact, and it touches server/escalation.py's
live AO-dispatch-critical-path retry mechanism (the exact 'multi-file rewrite of live-dispatch-critical-path machinery'
caution class), so a wrong partition choice risks a new starvation failure mode. Confirmed genuine and unchanged.

- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged.
- **context-scout 2026-08-20**: re-verified context_scope (5 entries), unchanged.

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- 624-line continuation of a fleet-wide QG capacity incident with 2 genuinely open todos and a dense evidentiary Progress Log (host-load readings, per-repo CI corroborations) through 2026-08-14. Item 1 (AWS Cost Explorer $ quantification) has been self-assessed 'bounded, worker-determinable, conflict-check clear' by 3 separate prior audits since 2026-08-01 but deliberately deferred to a future ci satellite-batch rather than extracted, and that batch pull has not happened across 7+ subsequent...
