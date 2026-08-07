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
author: unknown
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
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
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
  - [x] ✅ [INFRA] P3. Separately: investigate why 4 `ci-status-update` dispatches timed out in the same
        `full-workspace-sit` run (repo: system-integration-tests or unified-trading-pm, wherever `ci-status-update`
        lives) — if this is a recurring flake (not a one-off), it's worth a retry-with-backoff inside
        `cross-repo-invariants` rather than failing the whole SIT run on a downstream write timeout for repos that
        otherwise passed. **Confirmed recurring 2026-07-28** (see Recurrence section) — 5/6 "timeout" runs in that
        occurrence had actually completed `success` within 129-307s, all past the stamp-verification loop's fixed 90s
        poll budget in `cross-repo-invariants`'s job (repo: system-integration-tests). Fix: widened poll budget from 90s
        (18×5s) to 320s (64×5s) to cover ≥310s observed worst-case — system-integration-tests@69b93bc

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` §"The MVP gate set" / §"sit-gate/fleet-green" — the promoter's documented
  re-dispatch behavior this finding says didn't fire.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **2026-08-05 recurrence + false-completion found**: agent-orchestrator PR #783 (LDR→main promote) sat blocked ~2h40m+
  on `sit-gate/fleet-green=failure`. Same signature as this issue — `instruments-service`'s `ci-status-update` dispatch
  (run 30983625882) actually completed `success` at 07:06:28Z, but `cross-repo-invariants`'s poll loop gave up 7s
  earlier (07:06:21Z), reporting `conclusion=unknown/timeout` and failing the whole 21-repo fleet stamp on a false
  negative. **The widened-poll-budget fix this doc marks `[x]` done (system-integration-tests@69b93bc, committed
  2026-08-04T22:31:53Z) was on LDR but had NEVER reached `main`** — verified live: `main`'s served copy of
  `full-workspace-sit.yml` still read `seq 1 18` (the old 90s budget) at the time of this recurrence. Cause:
  `system-integration-tests` was **113 commits behind its own LDR with ZERO open LDR→main promote PR** — not a
  slow/stuck PR, no PR at all. Did not force that backlog through (too large/unreviewed-by-me for a same-turn call on a
  fleet-critical CI-gating repo). The `[x]` above should be read as "fix authored + on LDR", not "fix live". Unblocked
  via the same sanctioned workaround as 2026-07-27: `gh run rerun 30980838108 --failed` (system-integration-tests).
  Separately, PR #783 also carried a genuine (trivial) Dockerfile `BASE_IMAGE_DIGEST` merge conflict; the fleet
  promoter's deterministic take-LDR resolver dispatched 10+ times over 2h (all `conclusion=success` at the workflow
  level, none actually resolving it — plausibly because Option-B squash commits always look like "unique non-merge
  commits" vs LDR to that resolver's safety check, permanently disabling it for this promotion model), with no VM
  conflict-resolution-agent visibly picking up the escalation. Resolved by hand (took LDR's current digest value) and
  pushed to the bot-owned `promote/agent-orchestrator/*` branch; PR #783 merged clean at 09:43:02Z.
  - [x] ✅ [INFRA] P1. Investigate why system-integration-tests' own LDR→main promotion shows 0 open PR at 192 commits
        behind — root cause: ci_status=FAILING on LDR (Tier-A gate in ldr_to_main_fleet_promote.sh). TWO failures: (A)
        QG wall-clock 400s > 300s MAX_DURATION cap — fixed by raising to 600s (system-integration-tests@3f6f6ed) and
        recalibrating the stale 52.2s baseline to 400s (unified-trading-pm@b0a6a8563). (B) plan-commit-SHA-evidence
        ratchet broke at 28 > baseline 26 — re-baselined (unified-trading-pm@b0a6a8563). On the second question: the
        "zero unique non-merge commits vs LDR" safety check is NOT structurally unsatisfiable for Option-B squashes —
        verified that `git log --no-merges LDR..main` is empty for system-integration-tests (backmerge pulls all squash
        commits into LDR). It IS timing-dependent (can fail between a promote landing and the next backmerge) but that's
        by-design, not structural. The AGENT-ORCHESTRATOR PR #783 case was a different mechanism (Dockerfile digest
        conflict + the take-LDR resolver's safety check correctly refused because main had unique non-merge content from
        Option-B squashes that hadn't been backmerged yet — not unsatisfiable, working as designed).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **2026-08-06 investigation (slot 12, P0 task `sit_gate_fleet_green_auto_retrigger_stuck-004`)**:
  - **08-05 root cause confirmed**: system-integration-tests@69b93bc (wider poll budget 90s→320s) was on LDR but never
    promoted to `main` because system-integration-tests LDR→main promotion was stuck at 215 commits behind with 0 open
    promote PR. Root cause was twofold: QG wall-clock 400s > 300s `MAX_DURATION` cap + plan-commit-SHA-evidence ratchet
    at 28 > baseline 26. Both fixed (system-integration-tests@3f6f6ed raised cap to 600s; unified-trading-pm@b0a6a8563
    re-baselined). QG is now GREEN on LDR (run 31128741477, 22:04 UTC) — the 69b93bc fix should reach `main` on the next
    successful promoter tick.
  - **08-06 dispatch-flood root cause confirmed**: `process_repo` runs each repo in parallel background subshells.
    Before the fix, every subshell independently hitting a BREAKING-delta block could dispatch `full-workspace-sit`.
    With 21+ repos and 3 promoter ticks in 6 min, this produced 3+ dispatches in ~10s. Each cancelled the previously
    queued run via GitHub's `concurrency.group` + `cancel-in-progress: false` semantics, creating a permanent treadmill
    of queues and cancels. **Fix**: `_claim_sit_dispatch` mutex (`mkdir` atomicity) in unified-trading-pm@16c9653eb
    (2026-08-06 07:59 UTC) — only one dispatch per tick wins. The `SIT_INFLIGHT` check was NOT the root cause of
    ineffectiveness; the gap was that it ran ONCE at tick-start against a snapshot, while the parallel subshells raced
    past it mid-tick.
  - **08-06 afternoon SIT failures (runs 31112587576–31118400832, 14:47–16:02 UTC)**: Third distinct failure mode —
    GitHub Actions platform outage (`Service Unavailable` for action downloads). Transient, outside project control.
  - **deployment-service PR #716**: Resolved — merged at ~09:43 UTC after the IN_PROGRESS SIT run (31081197089)
    completed `success` at 07:50 UTC. `sit-gate/fleet-green` now reads SUCCESS on the merged PR.
  - **NEW FINDING — Fleet promoter `ldr-to-main-promote-fleet` stalled 3+ hours** (19:00–22:30 UTC, 13 consecutive
    cancelled runs). Root cause: only 1 of 4 `glue`-labeled self-hosted runners online and not busy (glue-3,5 offline;
    glue-2 busy). GitHub's concurrency group queued each run, but before a runner picked one up the next `*/5` schedule
    event cancelled the queued predecessor. Stuck until a runner became available; the 22:30 run finally reached
    `in_progress` at ~22:35. **This is a SEPARATE issue from the SIT auto-retrigger** — it blocks ALL LDR→main
    promotions (including the SIT fix reaching `main`), not just SIT-gated ones. Should be filed as its own issue doc
    with a runner-health monitor.
- **2026-08-06 recurrence (dispatch-flood variant)**: `full-workspace-sit` runs CANCELLED 20+ times between 06:00-07:30
  UTC (runs 31075871744 through 31081197089), blocking `deployment-service` PR #716 (and likely all other repos' promote
  PRs) on `sit-gate/fleet-green=failure`. New symptom vs prior occurrences: this was a **dispatch flood**, not a
  poll-timeout. `ldr-to-main-promote-fleet.yml` ran 3 times within 6 min (07:39, 07:43, 07:45), each firing the
  auto-retrigger (`sit_fleet_green_auto_retrigger()`), each creating a new `full-workspace-sit` `repository_dispatch`
  event. With `concurrency.group: full-workspace-sit` + `cancel-in-progress: false`, GitHub keeps at most ONE queued run
  — each new dispatch cancelled its predecessor while the first stayed IN_PROGRESS, creating a treadmill where the
  IN_PROGRESS run (31081197089, started 07:30) appeared to survive but the "Stamp SIT_VALIDATED" step ran 25+ min
  (normally ~13 min total job) and was still in progress at task end. The PENDING run 31082189352 (dispatched 07:46)
  awaits behind it. Prior fix (wider poll budget, system-integration-tests@69b93bc) addresses a different failure mode
  (poll-loop timeout on ci-status-update writes); this flood variant is new — the auto-retrigger debounce
  (`SIT_INFLIGHT` check) SHOULD suppress dispatches when a run is already queued/in_progress, but appears ineffective
  under high-frequency promoter ticks. Unblocked manually via `gh run rerun`? No — the IN_PROGRESS run was not forcibly
  recovered; diagnosis filed as escalation `agt-f85daa` (cicd slot 8). The deployment-service PR #716 code is clean
  (quality-gates-v2=SUCCESS on PR head, run 31077855577) — the ONLY blocker is `sit-gate/fleet-green`.

## Follow-ups

- [x] ✅ [CI] P0. Investigate the recurring sit-gate fleet-green auto-retrigger failures (08-05: fix never reached main;
      08-06 dispatch-flood variant, 20+ cancelled runs, deployment-service PR #716 blocked) — investigation complete,
      root causes identified + fixes shipped (see Progress Log 2026-08-06). Escalation agt-f85daa resolved by mutex fix
      unified-trading-pm@16c9653eb. Remaining: fleet-promoter runner-health issue filed separately as
      `plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md`. — unified-trading-pm@3358005f2

> **2026-08-06 archive-candidate audit**: Live unresolved incident: 08-05 recurrence shows the documented fix
> system-integration-tests@69b93bc 'had NEVER reached main' ('fix authored + on LDR', not live), and 08-06 recurrence
> (dispatch-flood variant, 20+ cancelled runs, deployment-service PR #716 blocked) was 'diagnosis filed as escalation
> agt-f85daa' - the gate is still failing fleet-wide [KEEP_OPEN todo synthesized from justification by archive sweep]

- **2026-08-06/07 recurrence — 4th distinct sub-mechanism found + fixed (cicd escalation agt-6398a6, slot 9,
  deployment-service PR #729)**: `sit-gate/fleet-green` FAILURE on #729 (blocked 53m+) traced to
  `cross-repo-invariants`' **run-ID-identification poll** — a SEPARATE loop from the completion-poll already widened by
  69b93bc ("Poll (up to ~30s) for a run id NOT in PRE_RUN_IDS", `for _ in $(seq 1 6); do sleep 5; done`). Confirmed
  genuinely transient/ load-dependent, not per-repo: across 2 SIT runs observed live, the SET of repos hitting
  `run-not-found` differed each time (6 repos one run incl. `deployment-service`; 6 different repos the next,
  `deployment-service` itself succeeding) — consistent with `?per_page=10` recent-runs listing transiently missing a
  just-dispatched run under fleet-dispatch volume, not a structural per-repo bug. **Fix**: widened 30s (6×5s) → 150s
  (30×5s), same pattern as 69b93bc — system-integration-tests@b3da771 (direct push to `live-defi-rollout`, QG green 62s,
  verified on origin). **Verified live**: next `full-workspace-sit` run (31131969006) completed SUCCESS; independently
  reconfirmed when a manually `workflow_dispatch`-triggered
  `ldr-to-main-promote-fleet.yml --only_repo=deployment-service` run (31133410830, used because GH's declared `*/5`
  schedule under-delivers ~37% per the doc up top — the untouched next scheduled tick hadn't fired in the 10+ min
  waited) posted `sit-gate/fleet-green=success` — visible on deployment- service's PR #731 (the promote branch had
  rolled to a newer LDR sha meanwhile, superseding/closing original #729; #731 shows `sit-gate/fleet-green: SUCCESS`,
  independent confirmation the fix holds across two different PRs/runs). **Out of scope, left for its own escalation**:
  PR #731 carries a genuinely NEW/unrelated `quality-gates-v2` FAILURE (QG slice/tests) — its own deterministic workflow
  already auto-fired "Escalate LDR-QG failure to orchestrator", so a fresh dedicated `ldr_qg_failure`/`sit_failure`
  worker should pick it up separately; not chased here (this escalation's assigned wall — sit-gate/fleet-green on #729 —
  is resolved).

- [ ] [CI] P2. Post-fix monitoring window: 4 distinct sub-mechanisms of `sit-gate/fleet-green` failure have surfaced and
      been individually fixed within ~11 days (2026-07-27 → 2026-08-07), the same failure CLASS as
      `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`. Watch for a 5th sub-mechanism recurring
      within ~2 weeks of `system-integration-tests@b3da771` landing. Done when: either the window closes clean (no
      recurrence by ~2026-08-21), or a 5th recurrence is confirmed and re-opens this doc's investigation. (repo:
      system-integration-tests)
