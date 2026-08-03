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

> **2026-08-02 line-cap remediation**: this doc hit 995/1000 lines (0 headroom) — every entry dated 2026-07-29 through
> the 2026-08-01 na-eligibility-audit was hoisted verbatim to
> `/plans/archive/2026_08/fleet_wide_qg_capacity_crisis_continues_day2_progress_log_history_2026_08_02.md` (mirrors the
> identical remediation this doc's own predecessor already got, 2026-07-29). Nothing below predates 2026-08-02.

- **2026-08-02 ~19:30-20:20Z (cicd escalation `agt-234224`, slot 6, `deployment-service`, `wall_type=ldr_qg_failure`,
  dispatched against promotion PR #672)** — same established signature, one more corroborating repo, plus a
  self-resolved-before-dispatch timing note. Dispatched because run
  [30747486206](https://github.com/IggyIkenna/deployment-service/actions/runs/30747486206) (PR #672,
  `promote/deployment-service/891f5a1637d2`, `pull_request`, created 12:16:29Z) failed both slices: `QG slice (checks)`
  hit the familiar hard basedpyright timeout (`❌ Type check FAILED/timeout (exit=124)`, 12:20:35Z→12:22:35Z, while the
  same job's `lint-codex` selector independently passed) and `QG slice (tests)` ran a genuinely enormous 7957s
  (2h12m37s) wall-clock before ending with 7 `pytest-timeout` (`>150.0s`) failures — 2856 passed / 7 failed, no other
  defects. `gh run list --workflow quality-gates-v2.yml --branch live-defi-rollout` shows the exact fleet-wide
  transition this doc tracks: every run before 2026-08-02T12:23Z that day was `success` in 4-6min (or ~25-30s on a
  content-hit fast-path); the three runs since (12:23:53Z, 15:24:38Z, 18:21:06Z) each ran 1-3h before being `cancelled`,
  and a fourth (`workflow_dispatch`, 19:27:46Z) was still `queued` 45min+ at investigation time — a hard, same-day onset
  matching this doc's established pattern exactly (cf. the `unified-trading-pm` 18:25→18:27Z hard transition entry
  above).

  **Reproduced locally FIRST, backgrounded per the mandatory pattern** (host reading at launch: `uptime` load average
  29.81/37.15/42.77 on 16 vCPUs — ~2.6x oversubscribed at the 1-min mark, worse at 15-min; 18 concurrent
  `quality-gates.sh --no-fix` processes already live on this shared host, `free -h` swap 24Gi/47Gi used — the identical
  oversubscription signature this doc has tracked since 2026-07-27, still live 6+ days later). `quality-gates.sh`
  self-throttled via its own `qg-host-governor.sh` admission control rather than blindly adding load. Result at current
  HEAD `e8963ecd6aba17685b73a5790e871ea2b05d0dbc`: tests slice **3018 passed, 5 skipped, 0 failed in 180.90s** (vs. CI's
  2h12m37s + 7 timeouts on the same suite) and the full gate **`✅ ALL QUALITY GATES PASSED (264s)`** (coverage
  71.86%≥70%, sentinel written matching HEAD) — a stark, decisive confirmation the code is 100% clean and the CI wall is
  pure host contention, not a regression. (Non-blocking corroborating detail: even this local run logged
  `⚠️ Resource drift: wall 264s > 2× baseline 106.0s` — some contention reached this box too, just nowhere near CI's
  multi-hour blowup.)

  **By the time this was diagnosed, the pipeline had already self-healed with no code change** — the exact
  self-merge-via-independent-signal pattern this doc already documents for instruments-service #1026/#1027/#1035 and
  features-service #902/#919: PR #672 merged at `12:16:31Z`, five seconds after creation and well before its own
  `pull_request`-triggered quality-gates-v2 run ever completed (merge commit `b935f4f1`). The _next_ fleet promote
  cycle, PR #673 (`promote/deployment-service/24e0878d65e6`), ALSO self-merged instantly (`14:47:16Z`) and its
  downstream `main-backmerge-to-ldr` + `Semver Agent` both ran `success` on the same push — i.e. the real business
  outcome (code promoted to `main`, backmerged, semver-tagged) completed successfully twice over, fully independent of
  whether the promote-PR's own confirmatory `quality-gates-v2` check ever went green. `gh pr list --state open` → empty
  (no PR currently open/blocked on this repo). The only residual redness is exactly that confirmatory check — PR#673's
  own run (`30752878298`) sitting mid-`tests`-slice for 2h+ and main's post-merge run (`30752882009`) `cancelled` after
  5h17m — both attributable to this doc's already-tracked incident, not to deployment-service's content.

  **Disposition: no code or workflow change made or needed.** Did not add a redundant CI retrigger: a
  `workflow_dispatch` retry on `live-defi-rollout` was already queued 45min+ at investigation start (`30763415950`) and
  PR#673's own confirmatory check was still actively executing (not stuck-queued) — per this doc's own established
  posture, a further dispatch on top of either would only add load to the same contended host, not help.
  `GET /api/repo-blockers` → `open: []` (nothing to fast-path). Pinged `AUTHORING_SLOT=ci` with the outcome (non-numeric
  literal — see whether it 400s/422s like the `ci-reconcile` literal this doc's prior entries already hit). Slot left
  clean on `live-defi-rollout`, no branch changes to `deployment-service` beyond this doc.

- **2026-08-02 ~21:40-21:50Z (cicd escalation `agt-e3d260`, slot 6, `strategy-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0` — direct LDR push, no PR)** — second same-day `strategy-service` corroboration of the identical
  `Type check FAILED/timeout (exit=124)` signature (first was the ~15:40 UTC entry in the parent doc
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`). Reproduced locally at current `live-defi-rollout`
  HEAD `a6689ca0` (backgrounded, heartbeated per the mandatory pattern): `bash scripts/quality-gates.sh` →
  **`✅ ALL QUALITY GATES PASSED (141s)`** — tests slice 5660 passed/248 skipped/22 xfailed/0 failed, coverage
  83.24%≥74% floor, basedpyright surfaced only its 7 pre-existing tolerated warnings (no timeout), codex-compliance gate
  3/4 violations (within tolerance, includes the known-tracked STEP 5.37 `greek_model.py` Reg-T threshold site).
  Cross-checked CI directly: `gh run list` shows the exact same HEAD (`a6689ca0`) has TWO runs — a completed `failure`
  (`30750125692`, 13:31:51Z, 6h31m wall time) and an `in_progress` retrigger (`30765248540`, started 20:16:33Z, not
  triggered by me) — both hitting `checks`-leg `basedpyright ... Type check FAILED/timeout (exit=124)` at the full
  documented `PYRIGHT_TIMEOUT`, identical to every other signature in this doc. Live host corroboration at diagnosis
  time: `uptime` load average **61.77/51.27/42.71**, swap **26Gi/47Gi** in use — same whole-host-thrashing signature, if
  anything worse than prior entries' 48-49 load-average readings. `gh pr list --state open` → `[]`,
  `GET /api/repo-blockers` → `open: []` — nothing currently blocked. **Disposition: no code/test/workflow change made or
  needed.** Did not add a redundant retrigger — a `workflow_dispatch` run was already `in_progress` on this exact HEAD
  at investigation start, and per this doc's established posture a duplicate dispatch onto an already-contended runner
  pool doesn't help. Did not touch `self_hosted_runner_labels` or the allowlist — `strategy-service` is one of the repos
  the 2026-07-28 operator ruling says to leave alone. Attempted to ping `AUTHORING_SLOT=ci-reconcile` per the standard
  completion step — `POST /api/slots/ci-reconcile/message` 422s (`slot_id` must be a valid integer; `ci-reconcile` is a
  non-numeric literal, same class of 422 this doc's `ci`/`ci-reconcile` precedents already hit). Slot left clean on
  `live-defi-rollout` (only this doc + `strategy-service`'s already-clean working tree touched — no commit made in
  `strategy-service`, nothing to leave dirty). Seventh repo-specific corroboration of the
  `Type check FAILED/timeout (exit=124)` signature class in this doc-pair, second specific to `strategy-service`.

- **2026-08-02 ~22:19-22:50Z (cicd escalation `agt-52cafa`, slot 5, `deployment-api`, `wall_type=main_ci_red`,
  `pr_number=0` — no promotion PR stuck; this is Option-B direct-push promotion)** — first `deployment-api`
  corroboration of the identical `Type check FAILED/timeout (exit=124)` signature, this time observed on `main` rather
  than a promotion PR. `main` HEAD `969bce0` (the tip of the last successful Option-B promotion, PR #476, merged
  15:18:38Z) failed `quality-gates-v2` twice on the SAME commit: the original `push`-triggered run (`30754060437`,
  15:18:46Z, `checks` leg 13m56s → `❌ Type check FAILED/timeout (exit=124)`, `tests` leg ran 2h15m51s before also
  failing) and a `workflow_dispatch` retrigger (`30767196199`, started 21:08:02Z, not triggered by me) that hit the
  identical `checks`-leg timeout again in 14m19s. `ERROR_COUNT=0`/`WARN_COUNT=0` on both — the
  `log_fail "Type check FAILED/timeout"` branch, not a real basedpyright finding. Separately, `live-defi-rollout` itself
  (currently 3 commits ahead of the promoted `main` tip: `aaa0d1d`/`34a596b`/`d1d2a21`) has NOT completed a fresh
  `workflow_dispatch` QG run since `12:23:51Z` (`b931b88`, success) — every subsequent dispatch (`15:24:36Z` 57m21s,
  `16:21:23Z` 3h6m50s, `19:27:43Z` 1h52m41s, all `cancelled`; `22:19:20Z` still `queued` 28min+ at investigation time)
  never completed, leaving the fleet-promote gate's cached `ci_status` stuck `FAILING` — confirmed live in
  `ldr-to-main-promote-fleet` run `30770288568` (22:31:35Z):
  `GATE BLOCK deployment-api: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`,
  correctly deferring promotion of the 3 newer LDR commits rather than a miss.

  **Reproduced locally FIRST, backgrounded per the mandatory pattern** (host reading at launch: load average
  32.44/33.71/35.07, swap 27Gi/47Gi used, 49 QG-related processes already live — same whole-host-thrashing signature as
  every other entry in this doc). `bash scripts/quality-gates.sh --no-fix` at current `live-defi-rollout` HEAD `d1d2a21`
  → **`✅ ALL QUALITY GATES PASSED (140s)`** — basedpyright completed clean with no timeout, all 100+ STEP-5.x
  codex/architectural checks green, sentinel written matching HEAD. Decisive confirmation the code is 100% clean and
  both the `main` push-triggered failures and LDR's own stuck dispatch chain are pure host contention, not a regression
  — the CONTEXT premise this escalation was dispatched with ("live-defi-rollout is GREEN") is correct at the content
  level even though the CI dispatch mechanism itself can't currently prove it.

  **Disposition: no code or workflow change made or needed.** Did not add a redundant retrigger on either branch — a
  `workflow_dispatch` run was already `in_progress` on `main`'s exact HEAD (`30767196199`, 1h39m+ elapsed) and another
  already `queued` on `live-defi-rollout` (`30769846668`, 28min+ elapsed) at investigation time; per this doc's
  established posture a duplicate dispatch onto an already-contended runner pool doesn't help. `gh pr list --state open`
  → `[]` (no promotion PR to unblock — Option-B direct push already landed the promotable content),
  `GET /api/repo-blockers` → `open: []` — nothing currently blocked. The fleet-promote gate's
  `GATE BLOCK ... ci_status= FAILING` behavior is itself correct (defers promotion of unverified-by-CI content) and will
  self-clear the moment any queued/in-progress dispatch on either branch completes green — not something to force.
  Attempted to ping `AUTHORING_SLOT=ci-reconcile` per the standard completion step — expect the same non-numeric-literal
  422 this doc's `ci`/`ci-reconcile` precedents already hit. Slot left clean on `live-defi-rollout` (only this doc
  touched; `deployment-api` working tree already clean, no commit needed there). Eighth repo-specific corroboration of
  the `Type check FAILED/timeout (exit=124)` signature class in this doc-pair, first specific to `deployment-api`.

- **2026-08-02 ~22:57-23:15Z (cicd escalation `agt-f70a66`, slot 4, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0` — Option-B direct-push promotion, same template as the `deployment-api` entry above)** — a DIFFERENT
  failure mechanism within the same root incident: not merely slow-but-progressing contention, a genuine DEADLOCK.
  `features-service` (one of the operator-ruled protected-6 self-hosted repos) gets exactly ONE dedicated glue-1 runner
  (`github-glue-runner-features-service@glue-1.service`) — confirmed via `systemctl`/`journalctl` on the runner host
  itself (this session runs on `i-172-31-5-118`, the same box). That single slot was monopolized by LDR's own
  `QG slice (tests)` job, started `21:11:27Z`, still "running" with **zero forward progress** at investigation time
  (~1h46m elapsed vs. this doc's own local reproductions of 141-264s): its `pytest` process was in kernel state **`D`
  (uninterruptible disk-sleep)**, ~0.1-2.6% CPU, `wchan=0` — a real hang, not GC/compute load — while host-wide `uptime`
  read load-average 32-35 on 16 vCPUs with 24-27Gi/47Gi swap in use (identical whole-host-thrashing signature this doc
  has tracked since 2026-07-27; other repos' pytest processes — `unified-api-contracts`, `ml-service` — were
  independently observed in the same `D` state at the same time, so this is fleet-wide, not features-service-specific).
  Because this repo's runner pool is `K=1` (unlike PM's 5+3), the wedge meant **main's own promotion-triggered
  `quality-gates-v2` run (`30749065832`) sat fully `queued` — never even started a job — since its `13:01:51Z` push**,
  and LDR's confirmatory run (`30763419660`) had a second job (`QG slice (checks)`) stuck `queued` behind the wedged one
  too. Unlike this doc's ~8 prior corroborations (where an `in_progress`/`queued` dispatch was making real if slow
  progress and the established disposition was "don't add load, let it self-resolve"), here NOTHING would resolve on its
  own short of GH Actions' 360-minute default job timeout — the runner had zero other jobs it could pick up while
  wedged, so main's queued run had no path to ever executing.

  **Disposition: killed the wedged process tree by exact PID** (SIGTERM then SIGKILL on `1786573`/`1786580`/`1787646`/
  `1786581`/`1787756`/`1787757` — the job-step bash script + `quality-gates.sh` + the hung `pytest` + their `tee`
  side-channels; never touched the `Runner.Listener`/`Runner.Worker` processes or any other repo's runner) — per
  CLAUDE.md's "confirmed runaway process endangering the host may be killed the same way (SIGTERM→SIGKILL) —
  investigate + doc it, don't wait on approval." This is a deliberate departure from the doc's established pure-observe
  posture, justified because the wedge was a hard deadlock (a stuck K=1 slot with no other job to run), not ordinary
  contention-slowness a duplicate dispatch would only worsen. Effect verified: the runner picked up the next queued job
  within ~35s (`journalctl`: "Job ... completed with result: Failed" at `23:04:21Z`, immediately followed by "Running
  job: QG slice (checks)" at `23:05:08Z`); `30763419660` moved `queued`→`in_progress`; main's `30749065832` remains
  queued behind it in normal FIFO order (expected with K=1, not a new wedge). In parallel, reproduced locally
  (backgrounded, heartbeated) at current LDR HEAD `529ec90e`: `bash scripts/quality-gates.sh --no-fix` reached 13%+ of
  the 18,299-item suite with zero failures before this entry was written — steady dot progress, not stalled,
  corroborating the code itself is clean and the wall was purely infra. Did not force a redundant `workflow_dispatch` on
  either branch — the now-freed queue drains on its own. Ninth repo-specific corroboration of the fleet-wide contention
  root cause, first to involve an actual kill-to-unwedge intervention rather than pure observation — worth the
  operator's attention if this K=1-deadlock failure mode recurs, since unlike PM's multi-runner pool, every protected-6
  repo with a single dedicated runner is structurally exposed to the same eternal-queue failure mode whenever ITS OWN
  prior job wedges, independent of overall fleet load level.

- **2026-08-02 ~22:20-23:31Z (cicd escalation `agt-42f50b`, slot 6, `unified-trading-api`, `wall_type=ldr_qg_failure`,
  `pr_number=0`)** — Tenth repo-specific corroboration, the "slow-but-progressing" class (not a deadlock): 4 CONSECUTIVE
  completed `quality-gates-v2` failures on `live-defi-rollout` HEAD `990187d`, spanning `13:32Z`→`23:27Z` (~10 hours),
  each run taking 45min-1h48m (`4111.99s`/`5704.25s`/unlogged/`2709.07s`) and each failing on a DIFFERENT random set of
  9-10 tests with `Failed: Timeout (>150.0s) from pytest-timeout` — near-zero overlap between runs' failing-test sets
  (checked pairwise), confirming scheduling-induced timeouts rather than a deterministic per-test bug. Local
  `bash scripts/quality-gates.sh` at the exact same HEAD: clean, fast, green — `441 passed` in `41.24s` (slowest local
  test 1.64s, nowhere near the 150s budget), `ALL QUALITY GATES PASSED (99s)` overall. This repo's glue runner is `K=1`
  (`github-glue-runner-unified-trading-api@glue-1`, confirmed via `systemctl`), same structural exposure the
  `features-service` entry above named, but this was NOT a deadlock (`D`-state/zero-progress) — every run genuinely
  executed and completed with real pass/fail counts, just severely slow. Corroborated live at investigation time:
  host-wide `uptime` load-average 29.8-35 (same box, `i-0c9b283b31d6b5ca7`-class), 29-30 concurrent `quality-gates.sh`
  processes across other slots. **Disposition: no code or test change made** — the code and tests are provably correct
  (clean local repro at HEAD); this is the tracked capacity crisis, not a regression, matching every prior entry's own
  established posture. Zero open `/api/repo-blockers` entries for `unified-trading-api` at investigation time. Did not
  force a 5th `workflow_dispatch` retrigger while the host remains this saturated — per this doc's established
  disposition, a duplicate dispatch onto an already-contended runner pool doesn't help and the queue/gate will
  self-clear once contention eases. Slot left clean on `live-defi-rollout` (nothing to commit in `unified-trading-api`;
  only this doc touched).

- **2026-08-02 ~23:20-23:32Z (cicd escalation `agt-ca1c32`, slot 5, `strategy-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0` — direct LDR push, no PR)** — third same-day `strategy-service` corroboration of the identical
  `Type check FAILED/timeout (exit=124)` signature (prior two: the ~15:40Z entry in the parent doc and the ~21:40-21:50Z
  entry above, escalation `agt-e3d260`), same HEAD `a6689ca0` throughout. Reproduced locally (backgrounded, heartbeated
  per the mandatory pattern): `bash scripts/quality-gates.sh` → **`✅ ALL QUALITY GATES PASSED (226s)`** — tests slice
  5660 passed/248 skipped/22 xfailed/0 failed, coverage 83.24%≥74% floor (identical figures to the ~21:40-21:50Z entry —
  same clean HEAD, no drift), basedpyright surfaced only its 7 pre-existing tolerated warnings, no timeout. Confirmed
  via `git diff --stat` that `a45069a9` (last CI-green SHA) → `a6689ca0` (current HEAD) contains only a CI-workflow-only
  change (`.github/workflows/quality-gates-v2.yml`, cancel-in-progress config) — no source touched — ruling out a
  genuine typecheck regression. Live CI cross-check: `gh run list` showed a THIRD run on this exact HEAD already
  `in_progress` at investigation start (`30772057438`, `workflow_dispatch`, not triggered by me); by the time I checked
  its `checks` leg had already failed the identical `basedpyright ... Type check FAILED/timeout (exit=124)` (its `tests`
  leg still running). Host corroboration: `uptime` load average **30.58/31.89/33.34**, swap **24Gi/47Gi** in use — same
  whole-host-thrashing signature as every other entry in this doc-pair. `gh pr list --state open` → `[]`,
  `GET /api/repo-blockers` → `open: []` — nothing currently blocked to fast-path. **Disposition: no code/test/workflow
  change made or needed.** Did not add a fourth redundant retrigger — a `workflow_dispatch` run was already
  `in_progress` on this exact HEAD at investigation start (its `checks` leg had already failed by the time I looked, but
  its `tests` leg was still making progress, and per this doc's established posture a duplicate dispatch onto an
  already-contended runner pool doesn't help); `strategy-service` is one of the protected-6 repos the 2026-07-28
  operator ruling says to leave on self-hosted / accept recurring reds / resolve via retrigger — not applicable here
  since a retrigger was already in flight. Did not force-resolve, lower a coverage floor, or pragma-skip anything — per
  the cicd role's hard rule, a wall this well-corroborated as pure infra contention (not a code/test defect) is not one
  a code change can fix. `POST /api/slots/ci-reconcile/message` expected to 422 (non-numeric `slot_id`) per this doc's
  `ci`/`ci-reconcile` precedents. Slot left clean on `live-defi-rollout` (only this doc touched; `strategy-service`
  working tree already clean, no commit needed there). Eleventh repo-specific corroboration of the
  `Type check FAILED/timeout (exit=124)` signature class in this doc-pair, third specific to `strategy-service`.

- **2026-08-02 ~23:20-23:50Z (cicd escalation `agt-68298f`, slot 5, `market-data-processing-service`,
  `wall_type=main_ci_red`, `pr_number=0` — Option-B direct-push promotion)** — twelfth repo-specific corroboration, a
  DIFFERENT failure shape within the same root incident: not the `checks`-leg basedpyright timeout, a `tests`-leg pytest
  hang. `main` HEAD `0f77552` (tip of the last successful Option-B promotion, PR #568, merged `13:16:43Z`) failed
  `quality-gates-v2` via `workflow_dispatch` (`30757463906`, created `16:48:28Z`, jobs actually ran `20:16-20:56Z`):
  `QG slice (tests)` step `Run quality gates (leg tests)` produced normal output through
  `Coverage floor: MIN_COVERAGE=70` then went silent for ~14min before a `PluggyTeardownRaisedWarning` /
  `OSError: cannot send (already closed?)` during `pytest_sessionfinish` teardown, exit=1, no genuine `FAILED tests/...`
  line anywhere in the log — a resource-starvation teardown crash, not an assertion failure. **Reproduced the identical
  signature on `live-defi-rollout` HEAD itself** (`9642cbb`, which already carries a correctly-scoped 1-line fix —
  `fix(mdps): streaming chain-bundle write path resolves output bucket, not source bucket`,
  `get_output_bucket_for_asset_group()` swapped in for `get_bucket_for_asset_group()`, 13 lines + a 3-line test-stub
  addition, reviewed and confirmed low-risk/targeted): run `30758737872` (`workflow_dispatch`, `17:22:44Z`) hit the
  exact same `Coverage floor` → 14min silence → `PluggyTeardownRaisedWarning`/`OSError: cannot send` → `exit=1` shape,
  this time after a 57min `QG slice (tests)` job. Same signature at TWO different commits including the one carrying the
  fix rules out a code regression as the cause. Confirmed via `git log 2ce1def..9642cbb` that only 9 small, incremental
  commits separate LDR's current HEAD from the last CI-green LDR run (`2ce1def`, `07:47:04Z`) — no large/risky change in
  the window either. Host corroboration at investigation time: `uptime` load average **32.60/28.42/29.62**, swap
  **20Gi/47Gi** in use, **25** concurrent `quality-gates.sh` processes already live on this shared host — the identical
  whole-host-thrashing signature every other entry in this doc tracks. Confirmed via the `ldr-to-main-promote-fleet`
  gate itself (`30772388512`, `23:30:36Z`):
  `GATE BLOCK market-data-processing-service: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`
  — the promotion gate is correctly deferring, not stuck/broken; it will self-clear the moment either branch's dispatch
  completes green. This repo's self-hosted runner pool is also `K=1` (`glue-ip-172-31-5-118-1`, confirmed via
  `GET /repos/.../actions/runners`) — same structural single-runner exposure the
  `features-service`/`unified-trading-api` entries above named, but NOT a deadlock here: a fresh `workflow_dispatch`
  retrigger on `live-defi-rollout` (`30772053085`, started `23:20:31Z`, not triggered by me) was actively making
  progress (`content sentinel` done, `QG slice (checks)` `in_progress`, `QG slice (tests)` queued behind it) throughout
  this investigation — genuine FIFO progress, not a stuck wedge, so no kill-to-unwedge intervention was warranted this
  time. **Disposition: no code or workflow change made or needed.** Did not add a redundant retrigger on either branch —
  a `workflow_dispatch` run was already `in_progress`/progressing on `live-defi-rollout`'s exact HEAD at investigation
  start, and per this doc's established posture a duplicate dispatch onto an already-contended `K=1` runner doesn't
  help. Did not force-resolve, lower a coverage floor, pragma-skip, or push anything to `main` — per the cicd role's
  hard rule (never force-fix LDR for a main-only problem, never push to protected `main`), and per this doc's
  established posture, a wall this well-corroborated as pure infra contention is not one a code change can fix; the code
  fix already on LDR (`9642cbb`) is correct and will reach `main` automatically via the next clean
  `ldr-to-main-promote-fleet` tick once a completed-green run updates `ci_status`. `gh pr list --state open` → `[]` (no
  promotion PR to unblock), `GET /api/repo-blockers` → `open: []` — nothing currently blocked to fast-path. Pinged
  `AUTHORING_SLOT=ci-reconcile` per the standard completion step. Slot left clean on `live-defi-rollout` (only this doc
  touched; `market-data-processing-service` working tree already clean, no commit needed there). Twelfth repo-specific
  corroboration overall, first to show the `tests`-leg `PluggyTeardownRaisedWarning`/`OSError: cannot send` hang shape
  (vs. the more common `checks`-leg basedpyright timeout).

- **2026-08-02 ~23:52-00:05Z (cicd escalation `agt-dbfcd7`, slot 7, `market-data-processing-service`,
  `wall_type=main_ci_red`, `pr_number=0`)** — near-duplicate dispatch of the `agt-68298f` entry immediately above (same
  repo, same wall_type, same HEADs — `main`@`0f77552`/`LDR`@`9642cbb`), independently re-derived the identical
  conclusion before spotting the prior entry: `main` is 326 commits behind LDR since the last successful promotion (PR
  #568, `13:16:43Z`); the push-triggered `quality-gates-v2` for that PR was `cancelled` (superseded), and every
  subsequent `workflow_dispatch` retry on both `main` and `live-defi-rollout` hit the same `Coverage floor` → ~14-17min
  silence → `PluggyTeardownRaisedWarning`/`OSError: cannot send (already closed?)` during `pytest_sessionfinish` →
  exit=1 shape, no genuine `FAILED tests/...` line anywhere. **Reproduced locally FIRST** (backgrounded, heartbeated):
  `bash scripts/quality-gates.sh --no-fix` at `live-defi-rollout` HEAD `9642cbb` →
  **`✅ ALL QUALITY GATES PASSED (98s)`**, sentinel written matching HEAD — decisive confirmation the code is clean,
  matching the prior entry's own local repro. Confirmed the fleet-promote gate (`ldr-to-main-promote-fleet` run
  `30773091668`, `23:50:58Z`) is correctly deferring:
  `GATE BLOCK market-data-processing-service: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`.
  Runner is `K=1` (`glue-ip-172-31-5-118-1`, `busy=true`); the same `workflow_dispatch` retrigger the prior entry
  observed in flight (`30772053085`, started `23:20:31Z`) was still genuinely progressing FIFO at investigation end
  (`checks` in_progress, `tests` queued behind it — not a deadlock) — over an hour queued/running, consistent with this
  doc's severe-contention signature, not a wedge. **Disposition: no code or workflow change made or needed** — did not
  add a redundant retrigger onto the same contended `K=1` runner; did not force-resolve or push to `main`. Pinged
  `AUTHORING_SLOT=ci-reconcile` per the standard completion step (expect the same non-numeric-literal 422 this doc's
  `ci`/`ci-reconcile` precedents already hit). Slot left clean on `live-defi-rollout` (only this doc touched;
  `market-data-processing-service` working tree already clean). Flagging for the operator/main-agent: this is the SECOND
  `main_ci_red` escalation dispatched for this exact repo+wall within ~30 minutes of each other (`agt-68298f` then
  `agt-dbfcd7`) — the escalation dispatcher may be re-firing on the same still-unresolved (but correctly-deferring, not
  broken) condition faster than a single `K=1` runner can clear its FIFO queue; worth checking whether
  `main_ci_red`/`ldr_qg_failure` dispatch should dedupe against an already-active escalation for the same repo+wall_type
  instead of spawning a fresh worker each retrigger cycle.

- **2026-08-02 ~23:34-23:50Z (cicd escalation `agt-d89fed`, slot 6, `strategy-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0` — direct LDR push, no PR)** — fourth same-day `strategy-service` corroboration of the identical
  signature this doc-pair has tracked since 2026-07-27. **Reproduced locally FIRST** (backgrounded, heartbeated):
  `bash scripts/quality-gates.sh` at `live-defi-rollout` HEAD `a6689ca0` → **`✅ ALL QUALITY GATES PASSED (112s)`**,
  sentinel written matching HEAD — decisive confirmation the code is clean (the peripheral-dir
  `e2e-testing/scripts/defi` basedpyright/ruff findings surfaced in the same run are pre-existing `log_warn`-only
  checks, non-blocking, unrelated to this wall). Checked 3 recent `quality-gates-v2` runs on `live-defi-rollout`:
  `30750125692` (`13:31:51Z`, 6h31m wall — job-level timestamps show `content sentinel` succeeded at `13:31:55Z` but
  `QG slice (checks)` didn't START until `17:36:47Z`, a 4h+ queue wait, not a stuck run), `30765248540` (`20:16:33Z`,
  2h30m wall, `checks` job: `❌ Type check FAILED/timeout (exit=124)` on the first typecheck attempt, retry fell back to
  `⚠️ Type check SKIPPED (--skip-typecheck flag)`, then `lint-codex` itself breached the wall-clock budget —
  `❌ Quality gates must complete in <300s (took 491s work...)`, with a `Resource drift: wall 491s > 2× baseline 131.2s`
  warning immediately above it — a runner-throughput signature, not a lint finding), and the then-`in_progress`
  `30772057438` (`workflow_dispatch`, started `23:20:38Z`) whose `checks` job (`91560807683`) had ALREADY failed by
  investigation time on the same `❌ Type check FAILED/timeout (exit=124)` signature (basedpyright timing out under
  `run_timeout`, not a real type error — no error listing follows it) while its `tests` leg was still `in_progress`,
  genuinely progressing FIFO (not a stuck wedge). Confirmed `strategy-service`'s runner pool is `K=1`
  (`glue-ip-172-31-5-118-1`, `online`, `busy=true` at check time) — same structural single-runner exposure this doc's
  other protected-6 entries document. `gh pr list --state open` → `[]` (no promotion PR to unblock);
  `GET /api/repo-blockers` → only one open entry, for `market-tick-data-service` (unrelated repo/root-cause) — nothing
  for `strategy-service` to fast-path. **Disposition: no code or workflow change made or needed.** Did not add a
  redundant retrigger — a `workflow_dispatch` run (`30772057438`) was already actively progressing on this exact HEAD at
  investigation start, and per this doc's established posture a duplicate dispatch onto an already-contended `K=1`
  runner doesn't help. Did not force-resolve, lower a coverage floor, pragma-skip, or touch `self_hosted_runner_labels`
  — `strategy-service` is one of the protected-6 repos the 2026-07-28 operator ruling says to leave on self-hosted /
  accept recurring reds / resolve via retrigger (not applicable here since a retrigger was already in flight). Pinged
  `AUTHORING_SLOT=ci-reconcile` per the standard completion step. Slot left clean on `live-defi-rollout` (only this doc
  touched; `strategy-service` working tree already clean, nothing to leave dirty). Fourth repo-specific corroboration of
  the `Type check FAILED/timeout (exit=124)` signature class in this doc-pair, third specific to `strategy-service`
  (after `agt-e3d260` ~21:40-21:50Z and `agt-ca1c32` ~23:20-23:32Z) — all three same-day `strategy-service` escalations
  independently landed on the identical non-code diagnosis, reinforcing the dispatcher-dedupe observation the entry
  immediately above already flagged.

- **2026-08-03 ~00:33-00:41Z (cicd escalation `agt-2c266f`, slot 4, `market-data-processing-service`,
  `wall_type=ldr_qg_failure`, `pr_number=0`)** — THIRD dispatch for this exact repo+wall within the same rolling window
  as the `agt-68298f`/`agt-dbfcd7` entries above (both `wall_type=main_ci_red`, ~23:20-00:05Z), same
  `PluggyTeardownRaisedWarning`/`OSError: cannot send (already closed?)` signature, one commit further ahead: LDR HEAD
  is now `beb9fed` (`fix(scripts): retry-idempotency gap in _copy_verify_delete()`, touches only
  `scripts/migrate_candle_canonical_2026_07.py` + its test — a one-off migration script, not the MDPS service path the
  failing `tests` slice actually exercises). Independently re-confirmed both failing runs this escalation was dispatched
  against (`30772053085` 23:20:31Z 1h7m48s, `30758737872` 17:22:44Z 5h55m56s) show the identical shape: `Coverage floor`
  line, then silence (16min / 14min respectively), then the teardown `OSError`, then `exit=1` 39-59min later — no
  `FAILED tests/...` line in either raw log (`gh api .../actions/jobs/<id>/logs`, not just `gh run view --log-failed`,
  to rule out CLI truncation hiding a real failure — confirmed genuinely absent, not hidden).

  **Reproduced locally FIRST** (backgrounded, heartbeated per the mandatory pattern) at current LDR HEAD `beb9fed`:
  `bash scripts/quality-gates.sh --no-fix` → **`✅ ALL QUALITY GATES PASSED (137s)`** — tests slice **2333 passed, 2
  skipped, 0 failed in 50.00s**, coverage 87.00%≥70% floor, sentinel written matching HEAD — decisive confirmation the
  code is clean at the exact HEAD CI is failing on. Live CI cross-check: a 4th `workflow_dispatch` (`30774747037`,
  started `00:33:20Z`) was genuinely progressing at investigation time — `content sentinel` job `success`,
  `QG slice (tests)` job `in_progress`, `QG slice (checks)` `queued` behind it (real FIFO progress, not a `K=1` deadlock
  like the `features-service` entry above). Runner `glue-ip-172-31-5-118-1` confirmed `online`/`busy=true` via
  `GET /repos/.../actions/runners`. Host corroboration at investigation time: `uptime` load average
  **44.47/39.62/33.59**, swap **20Gi/47Gi** in use, **26** concurrent `quality-gates.sh` processes already live on this
  shared host — same whole-host-thrashing signature every other entry in this doc-pair tracks, if anything worse than
  most prior readings. `GET /api/repo-blockers` → one open entry, unrelated repo (`market-tick-data-service`, a genuine
  pre-existing test-content issue, own issue doc) — nothing for `market-data-processing-service` to fast-path.
  **Disposition: no code/test/workflow change made or needed.** Did not add a redundant 5th retrigger — a
  `workflow_dispatch` run was already `in_progress`/progressing on this exact HEAD at investigation start, and per this
  doc's established posture a duplicate dispatch onto an already-contended `K=1` runner doesn't help. Did not
  force-resolve, lower a coverage floor, or pragma-skip anything. Slot left clean on `live-defi-rollout` (only this doc
  touched; `market-data-processing-service` working tree already clean, no commit needed there). Thirteenth
  repo-specific corroboration overall, second specific to `market-data-processing-service`, third dispatch for this
  exact repo+signature within ~90min — reinforcing the `agt-68298f`/`agt-dbfcd7` entries' own dispatcher-dedupe
  observation: the escalation dispatcher is re-firing on a still-progressing (not stuck) `K=1` FIFO queue faster than it
  can drain.

- **2026-08-03 ~00:36-00:44Z (cicd escalation `agt-6db91d`, slot 2, `market-data-processing-service`,
  `wall_type=ldr_qg_failure`, `pr_number=0`)** — FOURTH dispatch for this exact repo+wall within the same rolling window
  as `agt-68298f`/`agt-dbfcd7`/`agt-2c266f` above (all within ~90min), independently re-derived the identical diagnosis
  before finding the `agt-2c266f` entry immediately above it: both failing runs (`30758737872` 17:22:44Z, `30772053085`
  23:20:31Z, both against LDR HEAD `9642cbb`) show the same `Coverage floor` → 14-16min silence →
  `PluggyTeardownRaisedWarning`/`OSError: cannot send (already closed?)` teardown crash → `exit=1` shape, zero
  `FAILED tests/...` lines in either raw log; `checks` slice green both times. Did not re-run `quality-gates.sh` locally
  — `agt-2c266f` (3-8min earlier, same-class investigation) already verified `✅ ALL QUALITY GATES PASSED (137s)` at the
  current LDR HEAD `beb9fed` (one commit ahead of the failing SHA, an unrelated migration-script fix), and re-running
  the same gate on this already-oversubscribed host would only add load. Live CI cross-check: the same
  `workflow_dispatch` run `30774747037` (started `00:33:20Z`) `agt-2c266f` observed was STILL genuinely progressing at
  this check (`content sentinel` success, `QG slice (tests)` `in_progress`, `QG slice (checks)` `queued` — real FIFO
  progress, not a stuck wedge). `GET /api/repo-blockers` → `open: []` — nothing to fast-path. **Disposition: no
  code/test/workflow change made or needed.** Did not add a 6th redundant retrigger. This is the fourth escalation
  dispatched for the identical repo+wall condition in ~90min (`agt-68298f`, `agt-dbfcd7`, `agt-2c266f`, this one) —
  strongly reinforcing the dispatcher-dedupe gap those entries already flagged: consider this a fourth data point that
  the escalation dispatcher should dedupe against an already-active/recently-resolved escalation for the same
  `(repo, wall_type)` pair before spawning another one-shot worker, rather than relying on each new worker to
  independently re-discover "someone already handled this." Slot left clean on `live-defi-rollout` (only this doc
  touched; `market-data-processing-service` working tree already clean).

- **2026-08-03 ~01:36-01:50Z (cicd escalation `agt-bcc6bb`, slot 2, `deployment-api`, `wall_type=main_ci_red`,
  `pr_number=0`)** — a DIFFERENT downstream symptom of this same crisis, not the tests-teardown-crash signature the
  entries above track. `main`'s `quality-gates-v2` was RED (STEP 5.106 `check_bare_read_availability_index`: 2
  "non-baselined" bare `read_availability_index(bucket)` calls in
  `deployment_api/services/data_status_drilldown/ _core.py` at lines 171/388) while the boot context asserted
  `live-defi-rollout` was green. Root-caused via direct branch diff
  (`git log origin/main..origin/live-defi-rollout --oneline -- deployment_api/...`): `main` is **445 commits behind
  `live-defi-rollout`** for this repo — the specific commit that shifted `_core.py`'s line numbers
  (`aaa0d1d fix(data-status): ml-service manifest rollup used the sunset ml-models-store bucket alias`) landed on LDR
  but was never promoted, so `main`'s copy of the file still has the calls at 171/388 while the (already-promoted, PM
  repo) baseline yaml expects LDR's shifted 175/392 — a cross-repo promotion-timing skew (PM's own LDR→main promotion
  outran deployment-api's), not a code defect on either side. Confirmed via
  `unified-trading-pm/.github/workflows/ ldr-to-main-promote-fleet.yml`'s own latest run log (`30777006712`, PM repo):
  `GATE BLOCK deployment-api: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`
  — the fleet promoter itself refuses to promote deployment-api because it cannot observe a confirmed-green
  `quality-gates-v2` run on LDR, which is exactly this doc's root cause:
  `gh run list --branch live-defi-rollout --repo IggyIkenna/deployment-api` shows 5 consecutive `workflow_dispatch` runs
  CANCELLED back-to-back since the last real success (12:23:51Z 2026-08-02), all triggered by the same `IggyIkenna`
  automation actor spaced ~2-3h apart — each new dispatch cancels the prior run's `cancel-in-progress` concurrency group
  before it can finish a multi-hour run, so LDR's `ci_status` never resolves to a durable PASS and the 445-commit
  promotion backlog keeps growing. **Verified the actual code is clean, cheaply, without a full `quality-gates.sh`
  run**: ran the standalone checker directly against the local LDR checkout (`.tabs/2/deployment-api` at HEAD `dc7eece`,
  matching `origin/live-defi-rollout` exactly, clean tree) —
  `check_bare_read_availability_index.py --workspace-root . --scope deployment-api` →
  `OK — 9 baselined occurrence(s); 0 new occurrences`, confirming this specific gate step is genuinely green on LDR (not
  just a stale local read) at minimal host cost. Live CI cross-check: a 6th `workflow_dispatch` (`30777257322`, started
  `01:36:05Z`) was genuinely progressing at investigation time (`content sentinel` success, `QG slice (checks)`
  `in_progress`, `QG slice (tests)` `queued` — real FIFO progress). Host corroboration: `uptime` load average
  **42.60/39.95/38.00**, swap **18Gi/47Gi** in use — same whole-host-thrashing signature. **Disposition: no
  code/test/workflow change made or needed** — the fix already exists on `live-defi-rollout` (commit `aaa0d1d` among the
  445-commit backlog); hand-editing `main`'s baseline or file to force STEP 5.106 green would violate both the
  INTEGRATION-BRANCH RULE (never push to protected `main`) and the "don't re-fix code that's already green upstream"
  instruction — the correct fix is the pending promotion, which self-heals once LDR's `quality-gates-v2` completes one
  full uninterrupted run. Did not add a 7th redundant retrigger — a dispatch was already in flight and progressing; per
  this doc's established posture, a duplicate dispatch onto an already-contended host doesn't help and risks cancelling
  the one that's actually making progress. `GET /api/repo-blockers` → `open: []` — nothing to fast-path. Slot left clean
  on `live-defi-rollout` (only this doc touched; `deployment-api` working tree already clean, no commit needed there).
  New failure-mode data point for this incident: promotion-lag-induced `main`-only gate failures (distinct from the
  tests-teardown-crash signature above) are a second visible symptom of the same root cause, worth the fleet-promoter's
  dep-order/ci_status gate staying as the correct conservative behavior (it should NOT promote onto a repo whose LDR CI
  it can't confirm green) — the real fix is unblocking LDR's `quality-gates-v2` from completing a run at all, which is
  this doc's existing P1 thread, not a new one.
