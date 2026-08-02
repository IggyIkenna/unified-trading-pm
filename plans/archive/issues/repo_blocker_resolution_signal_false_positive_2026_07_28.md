---
doc_type: issue
title:
  repo-blocker resolution signal (watcher_green / reporter) fired twice while the underlying QG condition still failed
summary:
  Declared `RB-166e706f` for a genuine `market-tick-data-service` QG red (STEP 5.101 empty-string-fallback baseline
  breach — chronic, separately tracked in `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`).
  Received TWO consecutive "resolved" notifications (`resolve_source=watcher_green`, then `resolve_source=reporter` on
  the re-declared `RB-eb458809`) roughly 70 and 15 minutes apart respectively — both times a fresh, direct
  `check_no_empty_string_fallback.py --scope market-tick-data-service` re-run (repo confirmed at unchanged HEAD, zero
  new commits) reproduced the IDENTICAL failure both times. The condition never actually changed across all 3
  measurements; only the resolution signal did.
status: resolved
nature: issue
asset_group:
  [ao] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; content is an
  # agent-orchestrator repo-blocker resolution-signal false positive (repos: [agent-orchestrator]), squarely
  # ao-tranche; the MTDS QG red is only the triggering condition, not the subject.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [repo-blocker, multi-agent-safety, false-positive, reliability, quality-gates]
related:
  [
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: agent_operating_framework_master
source: "Self-observed by slot-14 during sports_track_h_denominator_prereqs-002, 2026-07-28"
resolved_by:
  "agent-orchestrator@a0f939b — ci_status() now gates staleness for every caller (root-caused via live gh API evidence,
  not speculation)"
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
---

> **🟢 ARCHIVED 2026-07-30** — status=resolved, archived per `/codex/11-project-management/issue-doc-lifecycle.md`'s
> archive-on-resolve rule (case 2: a commit SHA fixes the issue). Root-caused with live `gh api` evidence (not
> speculation — see Progress Log) and fixed at `agent-orchestrator@a0f939b`: `ci_status()` (the function backing BOTH
> `RepoHealthWatcher`'s poll loop and the documented `/ci-status` cicd verb) now applies the staleness gate
> (`failing_run_is_current`) uniformly, closing the gap that let `watcher_green` AND `reporter` both resolve a blocker
> off a stale "latest completed run" reading.

# repo-blocker resolution signal false-positive — 2026-07-28

## What I found

Timeline (all times UTC 2026-07-28):

1. **~13:45** — declared `RB-166e706f` after `quality-gates.sh --no-fix` genuinely failed STEP 5.101 (91
   empty-string-fallback sites > baseline 89, `scripts/verify_lst_collateral_support.py:89,167`).
2. **~14:56** — received
   `[orchestrator repo-health] market-tick-data-service is GREEN again (blocker RB-166e706f resolved via watcher_green)`.
   Fresh-pulled both `market-tick-data-service` and `unified-trading-pm` to `origin/live-defi-rollout` HEAD (zero
   pending commits either side), re-ran the FULL `quality-gates.sh --no-fix` — **identical failure**, same file, same
   line numbers, same counts (91 > 89).
3. **~15:14** — re-declared as `RB-eb458809` with this evidence.
4. **~15:34** — received
   `[orchestrator repo-health] market-tick-data-service is GREEN again (blocker RB-eb458809 resolved via reporter)`.
   Fresh-pulled `market-tick-data-service` again — `git rev-parse HEAD` unchanged (`873c6c73`, no new commits at all
   since step 2). Ran the TARGETED checker directly
   (`check_no_empty_string_fallback.py --scope market-tick-data-service`, faster than the full suite) — **identical
   failure again**, same 91 > 89, same 2 lines.
5. **~15:32** — re-declared a 3rd time as `RB-b6432008`.

**The underlying repo state genuinely never changed** across all 3 measurements (same HEAD SHA both times I checked it,
same live violation count both times I ran the checker). Only the orchestrator's own resolution signal fired twice,
incorrectly, from two DIFFERENT `resolve_source` values (`watcher_green` then `reporter`) — ruling out a single buggy
code path being the sole cause; this looks like two independent ways to reach an incorrect "resolved" state.

## Why it matters

The repo-blocker mechanism exists specifically so a worker doesn't have to self-poll a red repo (`worker.md` § 4b: "the
backend's RepoHealthWatcher then polls the repo's CI state ITSELF and, the moment it reads green, sends you an outbox
message"). If that signal is unreliable, EVERY waiter on a blocker is at risk of either (a) wasting time re-verifying a
false "resolved" signal (this session's cost: ~2 extra full/targeted QG runs, ~20 min), or worse, (b) a worker with LESS
verification discipline than this session applied trusting the signal and attempting to ship/quickmerge against a
still-red tree — which `quickmerge.sh`'s own Pass-1 QG gate would still catch (so no actual bad code reaches
`live-defi-rollout`), but would produce a confusing quickmerge failure disconnected from the worker's own (correctly
blocked) mental model.

## Recommended decision

1. **Did NOT attempt to root-cause the resolution-signal bug itself** — out of scope for this session (I don't have
   `agent-orchestrator`'s `RepoHealthWatcher`/reporter code open, and my actual task is unrelated data-pipeline work);
   flagging for whoever owns that subsystem.
2. **Established a local mitigation this session**: never trust a `resolved via <source>` notification at face value for
   a repo-blocker — always fresh-pull + re-run the SPECIFIC failing check (or full QG) before proceeding to ship. Worth
   promoting into `worker.md` § 4b's own text (currently reads "the green signal arrives as a message... act on it
   immediately" — this instance shows that's not always safe without a fresh local re-verify first).

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — root-caused with live evidence, fixed at `agent-orchestrator@a0f939b`.**
      Candidate angle 2 confirmed exactly: `ci_status()` (`server/ci_status.py`) computed `blocked` purely from the
      latest _completed_ `quality-gates-v2` run's conclusion, with ZERO check that the run describes current branch HEAD
      — `RepoHealthWatcher.tick_once()` separately re-applied `failing_run_is_current()` on top, but the `/ci-status`
      CLI verb (`ci_status()` called directly — what `agents/cicd.md` documents for a fixer to use) had no such gate, so
      ANY caller other than the watcher's own loop got an ungated, potentially-stale verdict. Verified live via
      `gh api repos/.../market-tick-data-service/actions/workflows/quality-gates-v2.yml/runs?branch=live-defi-rollout`
      for the exact incident window (2026-07-28 12:00–16:30 UTC): only 4 runs total, none matching the declarer's
      `873c6c73` HEAD — the run underlying the `reporter` resolution at 15:34 was still the 14:51:06 run
      (`head_sha=d7df92be`, ~43min stale), because the next dispatched run (15:47:36) was CANCELLED. A `reporter`
      fast-path caller almost certainly read this exact stale "success" via `/ci-status`. Fix: moved the staleness gate
      INTO `ci_status()` itself (added `stale` field to its payload; `blocked = qg_v2_state != "success" or     stale`)
      so every caller — watcher, CLI verb, and anything built on it later — shares one gate instead of each call site
      needing to remember to re-apply it; removed the now-redundant duplicate check from `repo_health_watcher.py`. 5
      new/updated tests (`test_ci_status_stale_green_is_blocked`, `test_ci_status_red_v2_never_checks_staleness`, + 3
      existing watcher tests updated to the new shape); full `quality-gates.sh` green (1995 passed, 0 failed). Candidate
      angle 1 (cached vs. live) and angle 3 (reporter keyed off a bad self-report) both resolve to the SAME root cause:
      the "latest completed run" read is live but can be stale relative to a fast-moving trunk, and nothing gated that
      staleness outside the watcher's own loop — not two separate bugs. (repo: agent-orchestrator)
- [x] ✅ [DOC] P3. **DONE 2026-07-30 — `unified-trading-pm/agents/worker.md` § 4b.** Added a short caution paragraph
      after the "act on it immediately" step, reflecting the actual fixed state rather than blanket distrust: the
      resolution signal is now staleness-gated fleet-wide (cites this issue + the fix SHA), but LDR is still a
      fast-moving trunk so a NEW unrelated commit can land between resolution and a waiter's own fresh-pull — ordinary
      trunk drift, not a signal bug, and the waiter's own quickmerge Pass-1 QG remains the final safety net (no need to
      preemptively re-run a full local QG on every resume). (repo: unified-trading-pm)

## Progress Log

- **2026-07-30 (slot-7, infra)** — Dispatched to investigate + fix. Read `server/repo_health_watcher.py`,
  `server/ci_status.py`, `server/ci_reconcile.py`, `server/routes/repo_blockers.py`,
  `server/state_store/repo_blockers.py` end to end. Initial hypotheses considered and REFUTED with evidence before
  landing on the real cause (recording for anyone re-investigating a similar signal-reliability gap):
  - _Promotion-PR conflation_ (a `pull_request`-triggered `quality-gates-v2` run for an LDR→main/staging promote PR
    sharing `head_branch=live-defi-rollout` with the hourly `workflow_dispatch` runs `ci_status()` polls) — REFUTED:
    `ldr-to-main-promote.yml`'s frozen-head migration (2026-07-18, "bug #7 guard") uses
    `PROMOTE_HEAD="promote/$REPO/${LDR_SHA:0:12}"`, not `live-defi-rollout`, so promotion-PR runs don't match the
    `?branch=live-defi-rollout` filter at all. Confirmed live: every run in the incident window had
    `event: workflow_dispatch`, zero `pull_request`.
  - _Content-sentinel (Firestore `qg_green_markers`) short-circuit_ serving a stale marker — considered but not pursued
    once the simpler, directly-evidenced mechanism (below) fully explained both `watcher_green` and `reporter`) without
    requiring a hash-key coincidence.
  - _STEP 5.101 silently excluded from the CI slice matrix_ (`QG_SLICE=lint-codex` vs. local's unsliced run) — REFUTED
    by reading `base-service.sh`: STEP 5.101 runs under `_QG_RUN_CODEX`, which the `lint-codex` slice sets `true`, same
    as a full run.
  - **Confirmed root cause** (`gh auth status` showed a live, authenticated `gh` — used real API calls instead of
    further speculation):
    `gh api ".../market-tick-data-service/actions/workflows/quality-gates-v2.yml/runs?branch=live-defi-rollout&per_page=100"`
    filtered to the incident window returned exactly 4 runs (12:38, 13:35, 14:51 success/`d7df92be`, then 15:47
    CANCELLED/`26c886356`) — a 56-minute gap with no completed run, spanning the entire `RB-eb458809` declare→resolve
    window (15:14→15:34). `repo_health_watcher.py`'s own `failing_run_is_current()` gate would have caught a STALE green
    (that's what it's for), but it was ONLY wired into the watcher's internal loop — `ci_status()` the function, and
    therefore the `/ci-status` CLI verb `agents/cicd.md` documents for a fixer to use, had no staleness check at all.
    `grep -rn "failing_run_is_current"` confirmed exactly one production call site (`repo_health_watcher.py:109`) before
    this fix.
  - **Fix**: `agent-orchestrator@a0f939b` — moved the gate into `ci_status()` (new `stale` field; `blocked` now accounts
    for it), simplified `repo_health_watcher.py` to trust `ci_status()`'s `blocked` directly. Updated
    `tests/test_ci_status.py` (+3 new tests) and `tests/test_repo_blockers.py` (2 watcher tests reshaped to assert at
    the `ci_status()` mock boundary instead of separately patching the now-removed
    `repo_health_watcher.failing_run_is_current` import). Full `quality-gates.sh --no-fix` green: 1995 passed, 0 failed,
    lint/format/basedpyright/frontmatter clean.
  - Host note: hit shared-`/tmp` disk-full (2GB tmpfs, 100% full from ~510 stale `pytest-of-ubuntu/pytest-N` dirs
    spanning ~5h) blocking pytest run — did NOT `rm -rf` shared `/tmp` state (the destructive-command guardrail
    correctly blocks that for an autonomous worker, and it's the right call — not this worker's call to make
    unilaterally about other slots' scratch state); instead redirected `TMPDIR` to the slot's own scratchpad (ample
    space on `/`) for both the targeted pytest run and the two full `quality-gates.sh` runs. Also hit the shared-host
    `≤max(2,floor(cores/4))=4` concurrent-full-QG cap (5 already running) — waited (bounded background poll, no
    busy-loop) rather than adding a 6th.
  - Archived per `issue-doc-lifecycle.md` case 2 (commit SHA fixes the issue) — no referrers found (`grep -rl` across
    `plans/` + `codex/` returned nothing), so no external banner/link fixes needed.
