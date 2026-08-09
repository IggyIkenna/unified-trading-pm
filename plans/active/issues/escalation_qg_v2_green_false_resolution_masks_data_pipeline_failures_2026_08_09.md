---
doc_type: issue
title:
  "escalation-queue `_poll_wall_resolution()` false-resolves 7 of 12 wall_types via an unrelated repo's quality-gates-v2
  conclusion — data_pipeline_failure escalations (99% of 604 historical rows) auto-close as qg_v2_green with zero worker
  ever dispatched, silently masking real (incl. CRITICAL) data-pipeline problems"
summary: >-
  Found by the 3-hourly `escalation_queue_reconciler` (dispatch `agt-21fadd`, slot 11) while triaging an unrelated
  odd-looking row (`agt-558c62`, unified-trading-pm `ldr_qg_failure` — that one turned out FINE, see Progress Log).
  `server/escalation.py`'s `_poll_wall_resolution()` (agent-orchestrator repo) is the single resolution-detection
  function used both by the pre-dispatch staleness re-probe (`retry_queued_escalations`) and the post-dispatch watchdog
  (`verify_dispatched_escalations`). For any `wall_type` not explicitly special-cased, it falls through to a generic
  check: "is the affected repo's OWN latest `quality-gates-v2` run, on the integration branch, green?" —
  `ci_reconcile.repo_ldr_qg_conclusion(repo)` — and if so, marks the escalation `resolved` (`resolution="qg_v2_green"`).
  That signal is a valid resolution proxy ONLY for `ldr_qg_failure` (bare or PR-scoped) and `main_ci_red` — wall types
  whose entire problem statement IS "is quality-gates-v2 green". It is **meaningless** for `data_pipeline_failure`,
  `provenance_blocked`, `sit_failure`, `sit_retry_cap`, `plan_health`, `harness_lint`, and `label_mismatch` — none of
  these problems have anything to do with the repo's routine CI conclusion, which is green the overwhelming majority of
  the time regardless. Confirmed live: two CRITICAL `data_pipeline_failure` escalations (a stalled backfill VM needing
  manual relaunch, and a CRITICAL 1%+ cell-loss data gap) were both auto-closed as `qg_v2_green` within ~4 minutes of
  being filed, with **zero worker ever dispatched** to look at either. DB history shows this is not an edge case:
  599/604 (99.2%) `data_pipeline_failure` rows, 80/80 (100%) `provenance_blocked`, 39/39 (100%) `sit_failure`, and
  221/222 `plan_health` rows all resolved via this same bogus signal — the `plan_health` figure directly contradicts
  that function's OWN docstring, which claims `plan_health` "return[s] None here and [is] closed by the watch-TTL, not
  falsely re-escalated" (it does not — the code and the docstring have diverged). This directly violates the workspace's
  "data pipeline correctness is the heartbeat" HARD RULE (`/codex/02-data/data-pipeline-correctness-hard-rule.md`): a
  `data_pipeline_failure` wall exists specifically to get a worker to read the filed DP issue and fix the root cause on
  LDR — for 12 days (earliest row 2026-07-28) that channel has been almost entirely a no-op.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    escalation-queue,
    ci-cd,
    ao-mechanism,
    data-pipeline-correctness,
    false-resolution,
    bug,
    escalation-watchdog,
    silent-failure,
  ]
related: [/plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md]
created: 2026-08-09
author: escalation_queue_reconciler (agt-21fadd, slot 11)
last_updated: 2026-08-09T05:30Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.36
assigned_role: escalation_queue_reconciler
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "escalation_queue_reconciler dispatch agt-21fadd (slot 11), 3-hourly scheduled check, 2026-08-09 ~05:17-05:30 UTC.
  Live examples: agt-143e6c (deployment-service, DP_VM_STALL/DP-VM-003), agt-a89836 (market-tick-data-service,
  DP_RUN_MOSTLY_EMPTY/DP-FETCH-009, CRITICAL). Blocked-question BLK-2a812311 raised to main (2026-08-09T05:2x UTC) —
  system returned an immediate 'Continue with: B' (file issue + notify operator, defer the code fix to a dedicated
  follow-up plan) with no further live message on `/api/slots/11/messages` in the bounded wait — treated as the
  effective answer per the skill's timeout-to-operator path; NOT a claim that main deliberated."
context_scope:
  [
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/ci_reconcile.py,
  ]
---

# escalation `_poll_wall_resolution()` false-resolves 7 of 12 wall_types via an unrelated CI signal

## What's broken

`agent-orchestrator/server/escalation.py::_poll_wall_resolution(repo, pr_number, wall_type)` (~line 1660) is the one
function both `retry_queued_escalations()`'s pre-dispatch staleness re-probe and `verify_dispatched_escalations()`'s
post-dispatch watchdog use to decide "has this wall cleared?". Its branching:

1. `pr_number and wall_type in _CONFLICT_RESOLVER_WALLS` (`merge_conflict`, `stuck_promotion_pr`) → PR merge-state
   check. Correct signal for these walls.
2. `pr_number and wall_type == "ldr_qg_failure"` → the PR's own head-branch `quality-gates-v2` conclusion. Correct —
   this wall's entire definition IS "did quality-gates-v2 pass".
3. **Fallthrough (everything else, including bare `ldr_qg_failure` with `pr_number=0`, AND every other `wall_type` in
   `WALL_TYPES`)**: `ci_reconcile.repo_ldr_qg_conclusion(repo)` — the repo's latest `quality-gates-v2` run on the
   integration branch, full stop. `== "success"` → `resolved("qg_v2_green")`.
4. `wall_type == "main_ci_red"` gets one more chance via the `main` branch's own conclusion.

Step 3 is correct for bare `ldr_qg_failure` and (as a secondary/legitimate check) `main_ci_red`. It is **wrong** for
every other member of `WALL_TYPES` (`agent-orchestrator/server/escalation.py` ~line 50): `data_pipeline_failure`,
`provenance_blocked`, `sit_failure`, `sit_retry_cap`, `plan_health`, `harness_lint`, `label_mismatch`,
`ldr_main_qg_failure` (this last one has its OWN quality-gates-v2 signal, but on the WRONG ref — see Todo 3). None of
these problems are "is the repo's routine CI green" — a repo's `quality-gates-v2` is green the large majority of the
time by default, so any open escalation of these types gets rubber-stamped `resolved` almost immediately, usually before
a worker is ever spawned.

The function's own docstring already states the intended contract: _"Walls with no machine-readable CI signal
(`plan_health`) return `None` here and are closed by the watch-TTL, not falsely re-escalated."_ The code does not do
this — `plan_health` hits the exact same fallthrough as everything else. Docstring and implementation have diverged;
this issue is about fixing the implementation to match the (correct) stated intent, generalized to every wall_type that
actually lacks a machine-readable signal.

## Live evidence (observed real-time during this check, 2026-08-09 ~05:17-05:20 UTC)

Two `data_pipeline_failure` escalations were queued and then closed within roughly 4 minutes, before any worker was ever
dispatched (`app log: "escalation <id> resolved before dispatch (qg_v2_green); closing, not spawning"`):

- **`agt-143e6c`** (repo=`deployment-service`) — context:
  `WARN DP_VM_STALL (DP-VM-003) — VM mtds-backfill-odds-smallchunk9 stalled — heartbeat 11m stale. RELAUNCH vm=mtds-backfill-odds-smallchunk9 launcher=launch-mtds-sports-odds-backfill-vm.sh ... Runbook: /codex/15-runbooks/incidents/rb_infra_relaunch.md.`
  Filed 05:16:53, "resolved" 05:20:40. **Nobody relaunched the VM** — the escalation closed itself on an unrelated CI
  signal.
- **`agt-a89836`** (repo=`market-tick-data-service`) — context:
  `CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) — high attempted_failed batch — asset_group=cefi data_type=book_snapshot_5: 9740 attempted_failed cells of 935218 attempted (ratio 1.0%) ... A backfill exited 0 / captured climbed but failed this batch invisibly.`
  Filed 05:16:30, "resolved" 05:20:39. **CRITICAL severity, zero investigation.**

Neither of these was checked against its actual problem (a stalled VM, a data-completeness gap) — both were closed
purely because `deployment-service`/`market-tick-data-service`'s unrelated `quality-gates-v2` happened to be green at
that moment. These two specific underlying problems are presumably **still live and unaddressed** right now (Todo 5).

## Historical blast radius (`agent-orchestrator/data/state/state.db`, `escalation_queue` table)

| wall_type                                                    | total rows                    | resolved via `qg_v2_green*` | %     |
| ------------------------------------------------------------ | ----------------------------- | --------------------------- | ----- |
| `data_pipeline_failure`                                      | 604 (2026-07-28 → now)        | 599                         | 99.2% |
| `provenance_blocked`                                         | 80 (2026-08-07 → 2026-08-08)  | 80                          | 100%  |
| `sit_failure`                                                | 39 (2026-07-28 → 2026-08-08)  | 39                          | 100%  |
| `plan_health`                                                | 222 (2026-06-29 → 2026-08-02) | 221                         | 99.5% |
| `ldr_qg_failure` (control — signal is VALID here)            | 906                           | 596                         | 66%   |
| `main_ci_red` (control — signal is VALID here, dual-checked) | 354                           | 226                         | 64%   |

Current `data_pipeline_failure` status breakdown: 599 `resolved` (false-positive), 4 `unresolved` (genuinely escaped to
cap — these 4 at least got a real worker), 1 `dispatched` (in-flight). Only 4/604 ever got a real shot at resolution via
the reescalation-cap path; the other 599 never got past the pre/post-dispatch staleness check.

`plan_health`'s last occurrence was 2026-08-02 (~7 days stale as of this writing) — worth checking whether a SEPARATE
fix already changed its dispatch path; `data_pipeline_failure`/`provenance_blocked`/`sit_failure` are all actively
recurring as of this check (data_pipeline_failure fired twice in the last 10 minutes of this session alone).

## Why this matters (HARD RULE)

CLAUDE.md: _"Data pipeline correctness is the heartbeat — an audit's issues are fixed in FULL (no deadline deferrals, no
asset_group skipped); only operator-gated BLOCKED-CREDENTIALS/-OPERATOR-DECISION/-UPSTREAM-OUTAGE defer."_ The
`data_pipeline_failure` wall_type is the mechanism that is supposed to turn a filed DP audit finding into an actual
worker fixing it on LDR (`agents/data_pipeline_failure.md`). For 12 days that mechanism has been almost entirely inert —
DP findings get filed, then silently closed unexamined, with no operator-facing signal that anything went wrong (no
page, no "abandoned" status — it reads exactly like a normal, healthy resolution in the dashboard). This is a **silent
failure mode**, the worst kind: the system looks healthy while doing nothing.

Mitigating factor: this workspace also runs independent DP self-healing/alerting infrastructure
(`/codex/05-infrastructure/data-pipeline-alerts.md`, the DP-* registry, `/data-pipeline-alerts-reconcile`) that may catch
and fix some of these same underlying problems through a different path — so "the escalation was false-resolved" does
not necessarily mean "the underlying data gap is still open" for all 599 historical rows. It DOES mean this specific
channel provides zero assurance either way, which is the actual defect.

## Step-3 ruling: main + operator overrode this session's own recommendation

Raised to main via `POST /api/slots/11/blocked` (`BLK-2a812311`) recommending **B** (file + notify, defer the code fix)
given the blast radius (shared resolution logic across 12 wall types, including the two — `ldr_qg_failure`,
`main_ci_red` — that currently work correctly). The endpoint's immediate synchronous response echoed "Continue with:
B", but the LIVE answer that followed went the other way: **main independently re-read
`server/escalation.py:_poll_wall_resolution` (lines 1660-1753) itself, confirmed the finding exactly as reported, and
answered `A`** (apply the scoped fix now) — reasoning that the fix is mechanical (it makes the code match its own
already-stated docstring intent, not a new design call), is provably non-regressive for the two currently-correct paths
(`ldr_qg_failure`/`main_ci_red`, both left untouched by construction — see the allowlist below), and that every
additional AutoSpawnLoop tick live risks more CRITICAL escalations being silently auto-closed with zero worker
dispatched — ongoing active harm under the data-pipeline-correctness HARD RULE, not a static finding safe to sit on.
**The operator's own final ruling on `BLK-2a812311` also came back `A`** (`disposition: final`), independently
confirming main's call. Proceeding to implement the fix + regression test in this same session per that ruling — see
Progress Log for the applied change (repo@sha).

## Todos

- [ ] [OPERATOR] P0. Confirm whether the two live-observed problems (DP-VM-003 stalled VM
      `mtds-backfill-odds-smallchunk9`; DP-FETCH-009 CRITICAL cefi `book_snapshot_5` 1% cell-loss gap on
      market-tick-data-service) are still unaddressed right now, and route them to whoever owns DP alert response if so
      — the escalation-queue channel that was supposed to catch these did not.
- [ ] P0. Research the TRUE resolution semantics (if any exist as a cheap machine-checkable signal) for each of:
      `data_pipeline_failure`, `provenance_blocked`, `sit_failure`, `sit_retry_cap`, `harness_lint`, `label_mismatch`.
      Default assumption per the function's own docstring intent: none of these have one, and `_poll_wall_resolution`
      should return `None` for all of them (same as the documented-but-unimplemented `plan_health` behavior) — they
      resolve only via an explicit signal from their own dispatched worker's own completion path, or via the
      reescalation-cap → `unresolved` → operator-paged path if never fixed.
- [ ] P0. Implement the fix: restrict the Step-3 `qg_v2_green` fallthrough in `_poll_wall_resolution` to an explicit
      allowlist (`ldr_qg_failure`, `main_ci_red`; confirm `ldr_main_qg_failure` per Todo 3) — every other wall_type
      returns `None` immediately. Add a REAL test (in-memory SQLite or equivalent, not a MagicMock stand-in — mirror
      `tests/test_escalation.py`'s `test_reconcile_prioritizes_recent_over_ancient_under_a_tight_limit` pattern) that
      asserts a `data_pipeline_failure` (or `provenance_blocked`) row is NOT auto-resolved by an unrelated green QG run,
      alongside a regression test that `ldr_qg_failure`/`main_ci_red` still correctly resolve via this signal.
- [ ] P1. `ldr_main_qg_failure` (PM's own LDR→main promotion PR QG failure) currently has NO `pr_number`-scoped special
      case in `_poll_wall_resolution` (only bare `ldr_qg_failure` gets one) — it falls through to the generic repo-trunk
      check instead of its OWN promotion PR's head-branch conclusion, the same stale-frozen-PR-checks bug class already
      fixed for `ldr_qg_failure` in 2026-08-06 (`escalation.py` docstring reference). Only 9 historical rows so low
      current blast radius, but worth folding into the same fix pass since it touches the identical code path.
- [ ] P1. Audit whether any recent (last ~7 days) `data_pipeline_failure` false-`resolved` rows correspond to DP alerts
      that are STILL firing today (cross-check against the live DP-* alert stream /
      `/codex/05-infrastructure/data-pipeline-alerts.md` registry) — if several are still-open, that is itself
      independent confirmation of real, currently-unaddressed data gaps, not just a theoretical risk.
- [ ] P2. Re-check `plan_health`'s false-resolution rate now that it appears to have gone quiet since 2026-08-02 —
      confirm whether a separate, already-shipped fix changed its dispatch path (it would not be surprising if
      `plan_health` resolution now happens some other way), so the fix's Todo 3 test coverage isn't accidentally
      redundant with something already shipped.

## Progress Log

**2026-08-09 (escalation_queue_reconciler, agt-21fadd, slot 11)**: Started from the skill's Step-1 cheap check
(`GET /api/escalations/active`) — two `queued` rows were seconds old (healthy), but a third (`agt-558c62`,
unified-trading-pm `ldr_qg_failure`, `attempts=52`, a `resolved_at` timestamp predating its own `dispatched_at`) looked
anomalous enough to warrant Step 2. Traced its full activity-log history: the wall has been genuinely, persistently red
for 6+ hours across 6 worker dispatches (slots 4→12→3→14→23→11), `reescalations=5` (under the `MAX_REESCALATIONS=10`
cap, no drift in any retuned constant), the one page-worthy miss (reescalation #3, prior=2 ≥
`PAGE_AFTER_REESCALATIONS=2`) correctly fired and correctly got cooldown-suppressed on the next two misses (confirmed
via `data/state/escalation_unresolved.dedup.json`'s `unified-trading-pm:ldr_qg_failure:reescalating` timestamp matching
exactly), and the huge `attempts=52` vs `reescalations=5` gap is fully explained by `retry_queued_escalations()` bumping
`attempts` (not `reescalations`) on every silently-logged failed retry (no-capacity / repo-collision) per the
intentional 2026-07-29 visibility fix — **not a bug**. `reconcile_stale_ unresolved_escalations()`'s ordering is still
`resolved_at.desc()` (not reverted to the fixed 2026-08-07 ascending bug) and is wired into
`AutoSpawnLoop._drain_escalations()`. Conclusion for that original row: **mechanism healthy**; the wall's own persistent
redness is `/ci-reconcile`/`cicd`-worker content scope, out of this skill's mandate, and plausibly (unconfirmed) the
same shared-host pytest-timeout contention class already tracked in
`/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md` and its chain.

While confirming the two `queued` rows resolved cleanly, watched BOTH auto-close via the generic `qg_v2_green` signal
within ~4 minutes of filing — despite being `data_pipeline_failure` walls with no relationship to QG. That observation
is what led to this doc; see body above for the full diagnosis, evidence, and blast radius. Filed this issue + raised
`BLK-2a812311` per the findings-triage HARD RULE (data-correctness big finding → notify operator + issue doc). No code
change made this session (see "Why this session did not apply the fix directly").
