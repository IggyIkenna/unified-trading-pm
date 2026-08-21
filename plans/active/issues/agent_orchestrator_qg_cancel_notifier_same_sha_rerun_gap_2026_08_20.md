---
doc_type: issue
title:
  agent-orchestrator "QG slice CANCELLED/TIMED-OUT" pages page correctly-by-design, but the same-sha-rerun case isn't
  recognized as non-actionable — a supersede-check blind spot, not a real timeout/OOM
summary: >-
  Two CRITICAL "QG slice CANCELLED / TIMED-OUT" Slack alerts fired for agent-orchestrator on 2026-08-20 (sha
  `0ec1f010d2` ~11:08Z, sha `25589117c3` ~11:39Z), part of the same CI-failures batch as the unified-api-contracts
  publish-ordering race (see related doc). For `0ec1f010`, confirmed via `gh run view --json jobs` +
  `gh api .../timing`: the run's `QG slice (tests)` and `QG slice (checks)` jobs were both `cancelled`, total run
  duration only ~209s (~3.5 min — too short for a genuine `timeout-minutes` hit or OOM), and the workflow's own
  `supersede-check` job ran and determined the sha was STILL the tip of `live-defi-rollout` at evaluation time (so it
  did NOT suppress the page — this is "working as designed" for the case it was built to catch). A SECOND run for the
  IDENTICAL sha (`0ec1f010`) completed `quality-gates-v2` = `success` about 3 minutes later. The alert was technically
  accurate (the run really was cancelled while being the ref tip) but functionally a false alarm: the same commit's
  very next run passed cleanly, seconds later. NOT YET ROOT-CAUSED to a specific trigger mechanism (what caused the
  second run to start) — that is the first open question below. NOT YET FIXED.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, github-actions, notifier, false-alarm, alerting, supersede-check, agent-orchestrator]
related:
  - /plans/active/issues/cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md
created: 2026-08-20
author: interactive session (slot-1) — operator-directed CI-failures triage
parent_epic: ci_master
priority: P3
source: "operator-directed CI-failures triage, 2026-08-20 16:23-16:49 IST Slack #ci-failures batch"
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-20
context_scope:
  [
    scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml,
    /codex/04-architecture/ci-alerting.md,
  ]
---

# agent-orchestrator QG cancel notifier — same-sha-rerun blind spot

## Evidence (measured, not inferred — confirmed for `0ec1f010` only)

- Run `32362061775` (agent-orchestrator, sha `0ec1f010d21e7a68230ea7ef88c5c13344eb175d`, push to
  `live-defi-rollout`, started 2026-08-20T11:04:59Z). `gh run view 32362061775 --json jobs`:
  - `QG slice (tests)`: `cancelled`
  - `QG slice (checks)`: `cancelled`
  - `supersede check`: `success`
  - `quality-gates-v2` (aggregate): `failure`
  - `Slack CRITICAL — QG Slice Failed / send-notification`: `success` (i.e. it DID post)
  - `Slack INFO — QG Recovered`: `skipped`
- `gh api repos/IggyIkenna/agent-orchestrator/actions/runs/32362061775/timing` → `run_duration_ms: 209000` (~3.5 min).
  Genuine `timeout-minutes` hits and OOM kills in this workspace's QG runs are documented elsewhere as running far
  longer before termination — this duration doesn't fit either signature.
- A second run for the SAME sha, `32362310627`, started ~11:08:01Z (≈3 min after the first was cancelled) —
  `quality-gates-v2` = `success`.
- `python-quality-gates-v2.yml`'s `supersede-check` job (lines ~1002-1042 of
  `scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`) exists specifically to distinguish "a
  NEWER push superseded this run" (suppress) from "this run is genuinely cancelled while still the ref tip" (real,
  page) — built after a 2026-07-16 incident documented inline in that file. It compares `GITHUB_SHA` of the run
  against the CURRENT tip of the ref via `gh api repos/.../commits/${GITHUB_REF_NAME}`. Since `0ec1f010` was still the
  tip at evaluation time (no newer push had landed), `superseded=false` and the notifier fired — correctly, by its own
  documented logic.
- Second occurrence same day: sha `25589117c3910256f722b271de05e45eace31179` (~11:39Z), same
  `image-build-vm-orchestrator` job failure signature as `0ec1f010` — but that specific failure is a SEPARATE, already
  self-documented, by-design non-issue ("Expected failure: Dockerfile.vm-orchestrator requires a gar_token secret...
  Not a workflow bug — see this file's STATUS header", no GCP WIF creds configured for that workflow yet). **NOT
  independently confirmed** whether `25589117`'s own `quality-gates-v2` run followed the identical
  short-cancel-then-same-sha-retry-succeeds pattern — the job list for that run was not pulled this session. Do not
  assume it matches; verify before citing it as a second confirmed instance.

## Working theory (NOT fully confirmed — first thing to verify)

`supersede-check`'s tip-comparison correctly handles "a NEWER commit was pushed, cancelling this run" — the sha
changes, the check sees a new tip, suppresses. It does NOT have a check for a DIFFERENT case: a second workflow run
dispatched for the exact SAME sha (a manual "re-run failed jobs" click, an automated retry actuator, or a duplicate
trigger) that shares this workflow's concurrency group and cancels the first run via GitHub's own concurrency-group
cancellation semantics. Since the sha is unchanged, the tip-comparison sees `TIP == GITHUB_SHA` and treats the
cancellation as real/authoritative — which it is, in the narrow sense that the run really was cancelled — but it's not
actionable, because the identical commit's very next attempt passed.

**This is a theory, not a confirmed mechanism.** What actually triggered the second run for `0ec1f010` (manual rerun?
an automated retry actuator? something else?) was not identified this session — that's the real first step for
whoever picks this up, before designing a fix. Confirming the concurrency `group:` key this workflow actually uses
(inferred here, not read directly) is part of that.

## Why this matters (and why it's low priority)

Cosmetic Slack noise, not a real pipeline break — the underlying commit was genuinely fine 3 minutes later, and
nothing was left broken. Filed because: (1) it will keep recurring on every future same-sha rerun-while-in-flight
until closed, and (2) it's a distinct, previously-undocumented gap in an alerting mechanism this workspace already
invested in getting right for the sibling case (`supersede-check`'s 2026-07-16 fix) — worth tracking rather than
re-diagnosing from scratch the next time it pages.

## Todos

- [ ] [CICD] P3. **Confirm the trigger mechanism** for the second same-sha run — was `0ec1f010`'s retry a manual
      "re-run failed jobs," an automated actuator, or something else? Needed before designing a fix (the right
      suppression condition may differ depending on the answer).
- [ ] [CICD] P3. **Design + extend `supersede-check`** (or add an adjacent check) to also recognize "a later run for
      this exact sha already exists and reached `success`" as suppressible, mirroring the existing newer-sha logic.
      Note a real ordering constraint: at the moment the cancelled run's own notify step evaluates, the retry run may
      not have started/finished yet — a naive "check for a later successful run" would race. Think through whether
      this needs the RETRY run itself to also emit a recovery signal (there's already a skipped "Slack INFO — QG
      Recovered" step in this workflow — investigate whether wiring that in for the same-sha case is simpler than
      extending `supersede-check` itself).
- [ ] [CICD] P3. **Verify whether `25589117` matches the same pattern** — pull its `quality-gates-v2` job list and
      run timing before citing it as a second confirmed instance of this specific gap.

## Progress Log

- **2026-08-20 (interactive, slot-1)** — Filed during operator-directed CI-failures triage (same batch as the UAC
  publish-ordering race, see related doc). Confirmed the cancel-then-same-sha-retry-succeeds pattern for `0ec1f010`
  via direct `gh run view`/`gh api` evidence; confirmed `supersede-check` is working exactly as its own documented
  logic intends (this is a gap in that logic's coverage, not a bug in what it currently checks). Did not implement a
  fix or fully confirm the trigger mechanism — scoped as follow-up work for whoever picks this up next.

**na-eligibility-audit 2026-08-21** (ci tranche wave 2, first audit pass — doc filed 2026-08-20): KEEP-NA, valid.
All 3 open todos are investigation/design work, none worker-determinable alone: (1) confirm the trigger mechanism
for the second same-sha run — the doc's own "Working theory" section states this explicitly ("NOT fully confirmed —
first thing to verify... What actually triggered the second run... was not identified this session"); (2) design +
extend `supersede-check` to recognize a later-same-sha success as suppressible — the doc itself flags a real race
condition to think through (the retry run may not have finished when the cancelled run's notify step evaluates),
a genuine design call, not a mechanical patch; (3) verify whether a second alert (`25589117`) matches the same
pattern — an open investigation, explicitly "NOT independently confirmed" per the doc's own STATUS section. Low
priority (P3, "cosmetic Slack noise, not a real pipeline break" per the doc's own framing). No `assigned_vm` change.
