---
doc_type: issue
title:
  "sit-gate/fleet-green stayed RED for 2h+ blocking LDR→main promote PRs fleet-wide — the documented 'promoter
  re-dispatches full-workspace-sit on red each tick' auto-heal did not fire across 2 promoter ticks"
summary: >-
  Discovered while verifying instruments-service PR #982 (carries the sports-enum OOM durable fix, commit 5134a5f0) was
  blocked from merging to main. `sit-gate/fleet-green` read `failure` because the last `full-workspace-sit` run
  (system-integration-tests run 30258599465, 2026-07-27T10:34:32Z) failed on `cross-repo-invariants` — but the actual
  failure was 4 downstream `ci-status-update` dispatches timing out ("conclusion=unknown/timeout") for
  alerting-service/greeks-service/instruments-service/unified-trading-system-ui, not a real cross-repo invariant
  violation. Per /codex/08-workflows/ci-cd-flow.md, "On a red/absent signal the PR stays BLOCKED until a later tick
  reads a green SIT" and the promoter is documented to actively re-dispatch full-workspace-sit on red. In practice, the
  PM fleet promoter (ldr-to-main-promote.yml) ran successfully at 2026-07-27T11:26:02Z and 2026-07-27T12:38:50Z (2
  ticks, ~2h after the red) with NO corresponding new full-workspace-sit run appearing in system-integration-tests — the
  auto-retrigger did not fire. Manually triggered `gh workflow run full-workspace-sit.yml` (workflow_dispatch, run
  30266902462) as an unblock; this is a sanctioned, low-risk action (no destructive/mutating side effects, fleet-wide
  benefit) but should not be the standing recovery path.
status: open
nature: issue
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm, system-integration-tests]
scope: [engineer]
tags: [ci-cd, sit-gate, fleet-promoter, ldr-to-main, flaky, ci-status-update]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/sports_is_daily_enum_backfill_oom_at_32gi_ceiling_2026_07_27.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source:
  [
    "Surfaced while verifying instruments-service PR #982 (slot-13, 2026-07-27) — the fix it carries was blocked from
    reaching the deployed Cloud Run image by this stuck gate.",
  ]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    .github/workflows/ldr-to-main-promote-fleet.yml,
    /plans/archive/issues/sports_is_daily_enum_backfill_oom_at_32gi_ceiling_2026_07_27.md,
  ]
assigned_vm: planning
resolved_by:
---

# sit-gate/fleet-green auto-retrigger did not fire across 2 promoter ticks after a red SIT run

## What I found

1. `system-integration-tests` run 30258599465 (`full-workspace-sit`, 2026-07-27T10:34:32Z) failed on the
   `cross-repo-invariants` job — but the actual error lines show 4 `ci-status-update` dispatch calls timing out
   (`conclusion=unknown/timeout`) for alerting-service, greeks-service, instruments-service, unified-trading-system-ui —
   not a real invariant violation (21/21 repos otherwise stamped `SIT_VALIDATED` cleanly). This reads as a transient
   infra flake (GH Actions dispatch/Firestore-write timeout), not a code defect.
2. `/codex/08-workflows/ci-cd-flow.md` documents: "the fleet promoter computes... POSTS it... On a red/absent signal the
   PR stays BLOCKED until a later tick reads a green SIT" — implying the promoter actively re-drives SIT to recover. The
   PM fleet promoter (`ldr-to-main-promote.yml`) ran successfully (its own workflow conclusion) at
   `2026-07-27T11:26:02Z` and `2026-07-27T12:38:50Z` — 2 ticks spanning ~2h after the red SIT run — with **no new
   `full-workspace-sit` run appearing** in `system-integration-tests` in that window (confirmed via
   `gh run list --repo IggyIkenna/system-integration-tests --workflow=full-workspace-sit.yml`).
3. This left `sit-gate/fleet-green` stuck RED, which blocked `instruments-service` PR #982 (`mergeStateStatus: BLOCKED`)
   — and, being a fleet-shared signal, would have blocked EVERY `ldr_main` repo's pending LDR→main promote PR
   simultaneously, not just mine.
4. Unblocked by manually running `gh workflow run full-workspace-sit.yml --repo IggyIkenna/system-integration-tests`
   (its `workflow_dispatch: {}` trigger) — run 30266902462, started 2026-07-27T12:40:44Z.

## Recurrence — 2026-07-28

Recurred within 24h, same failure class, now with precise root-cause evidence for the P3 item below. Discovered while
resolving `ldr_qg_failure` escalation `agt-c3b95e` (strategy-service PR #448, closed/superseded by #449) — #449's own
`quality-gates-v2` is GREEN (both on the PR head and on `strategy-service`'s `live-defi-rollout` directly), but the PR
stayed `mergeStateStatus: BLOCKED` on `sit-gate/fleet-green`, sourced from `full-workspace-sit` run 30318661102
(2026-07-28T00:53:28Z, conclusion=failure).

Root cause is now precisely quantified: `cross-repo-invariants`' stamp-verification loop polls each dispatched
`ci-status-update` run for **up to 90s** (`for _ in $(seq 1 18); do ... sleep 5; done`) before giving up and marking it
`conclusion=unknown/timeout`. Checked all 6 runs the SIT job reported as timed-out/failed directly
(`gh run view <id> --repo IggyIkenna/unified-trading-pm`) — **5 of 6 had already completed with `conclusion=success`**,
just AFTER the 90s window closed (observed actual durations: ml-service 129s, strategy-service 148s,
trading-agent-service 307s, unified-api-contracts 303s, unified-trading-library 145s — all self-hosted `glue-writer`
runner jobs). Only 1 of 6 (unified-trading-api, run 30320312155) was a genuine `conclusion=failure` (620s runtime before
failing; job log expired/`BlobNotFound` by the time this was checked, so root cause of that specific failure is
unconfirmed). So the SIT gate is failing predominantly on a **poll-timeout sized for a runner-speed assumption that no
longer holds**, not on real cross-repo invariant breaks — confirms and quantifies the P3 hypothesis below.

At time of writing, a new `full-workspace-sit` run (30327524879, `schedule` trigger, started 2026-07-28T04:00:53Z) was
already in flight — consistent with this being genuinely recurring/frequent rather than a one-off. Did not wait for it
synchronously (one-shot bounded task, shared CI-firefighter capacity) — a fresh SIT run finishing green will clear the
gate for #449 same as for any other currently-blocked promote PR fleet-wide once the promoter's next tick reads it (or
sooner if the retrigger-reliability question above turns out to matter here too).

## Why it matters

If the promoter's on-red re-dispatch genuinely isn't firing (vs. e.g. only firing under a narrower condition than "any
open promote PR blocked on a red gate"), every transient SIT flake becomes a fleet-wide multi-hour promotion stall that
nobody notices until a worker happens to be blocked on it and manually intervenes — which is exactly what happened here.
This is the same failure CLASS as the `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` issue
(fleet-wide gate + no visible self-heal), just a different trigger condition.

## Recommended decision

- [x] ✅ [INFRA] P2. Find and read the actual re-dispatch condition in `ldr-to-main-promote.yml` /
      `ldr-to-main-promote-fleet.yml` (repo: unified-trading-pm) — confirm whether it re-fires `full-workspace-sit` via
      `repository_dispatch` on every tick it reads a red/stale `sit-gate/fleet-green`, or only under a narrower
      condition (e.g. only once per red-transition, or gated on a debounce window that hadn't elapsed). If the
      re-dispatch call is present but silently failing (e.g. a `gh api ... dispatches` call erroring without failing the
      promoter job), fix the error handling so it's loud, not silent. — unified-trading-pm@d0093938a
  - **Finding**: `ldr-to-main-promote.yml` (PM's own single-repo drain bot) never references `sit-gate/fleet-green` or
    `full-workspace-sit` at all — irrelevant to this gap. `ldr-to-main-promote-fleet.yml` computes `SIT_FLEET_STATE`
    each tick (`gh run list` on `system-integration-tests`'s `full-workspace-sit.yml`) but, before this fix, used it
    **only** to POST the `sit-gate/fleet-green` commit status — there was no code path reacting to a red reading at all.
    The ONE existing `full-workspace-sit` `repository_dispatch` call in the file (inside `process_repo`, reason
    `ldr-main-breaking-gate`) fires for a SIT-covered repo's own unvalidated BREAKING/unknown delta on its exact LDR
    tree — a condition **entirely independent** of `SIT_FLEET_STATE`. So the answer to the question this todo asked is
    neither "re-fires on every red tick" nor "silently failing" — **the re-dispatch-on-red mechanism did not exist at
    all**. codex's phrasing ("the PR stays BLOCKED until a later tick reads a green SIT",
    `/codex/08-workflows/ci-cd-flow.md` line 583) is passive and technically accurate; the issue's opening summary read
    an active "auto-heal" into it that the code never implemented.
  - **Fix shipped**: added `sit_fleet_green_auto_retrigger()` to `ldr-to-main-promote-fleet.yml`, called right after
    `SIT_FLEET_STATE` is computed. When the signal reads `failure`, it dispatches a fresh `full-workspace-sit` run
    (`event_type: full-workspace-sit`, `reason: fleet-green-red-retrigger`) unless a `full-workspace-sit` run is already
    `queued`/`in_progress` (debounce, reusing the already-fetched `SIT_LAST_RUN_JSON`) — so a transient flake now
    self-heals on this bot's own next ~5-15 min tick instead of waiting on the sparser nightly cron or a coincidental
    BREAKING-delta dispatch elsewhere. A failed dispatch call logs a loud `::warning::`, never silent. Regression test:
    `scripts/quality-gates-base/tests/test-sit-fleet-green-auto-retrigger.sh` (extracts the real function body, dedents
    it per the established `textwrap.dedent` technique, proves red+no-run-in-flight dispatches, red+in-flight debounces,
    green never dispatches, and dry-run never calls `curl`) — 6/6 pass.
  - [ ] [INFRA] P3. Separately: investigate why 4 `ci-status-update` dispatches timed out in the same
        `full-workspace-sit` run (repo: system-integration-tests or unified-trading-pm, wherever `ci-status-update`
        lives) — if this is a recurring flake (not a one-off), it's worth a retry-with-backoff inside
        `cross-repo-invariants` rather than failing the whole SIT run on a downstream write timeout for repos that
        otherwise passed. **Confirmed recurring 2026-07-28** (see Recurrence section) — 5/6 "timeout" runs in that
        occurrence had actually completed `success` within 129-307s, all past the stamp-verification loop's fixed 90s
        poll budget in `cross-repo-invariants`'s job (repo: system-integration-tests). Fix: widen the poll budget (e.g.
        `seq 1 18` → cover ≥310s observed worst-case, or make it adaptive) rather than retry-with-backoff alone — the
        runs ARE succeeding, the gate is just not waiting long enough to see it.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` §"The MVP gate set" / §"sit-gate/fleet-green" — the promoter's documented
  re-dispatch behavior this finding says didn't fire.
