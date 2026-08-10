---
doc_type: issue
title: >-
  Promote-bot fix verified for its own mechanism, but measurement found the ACTUAL dominant churn source is
  quickmerge.sh's Option-B direct PR (head=live-defi-rollout) — still unfixed
summary: >
  Started as a verification tracking note for the `ldr-to-main-promote.yml` / `ldr-to-main-promote-fleet.yml` fix
  (commit `48800b7ad`, merged via PR #1674) — that fix is real and correct FOR ITS OWN MECHANISM (the standing cron
  bot's frozen-per-SHA-ref promote PRs no longer get superseded mid-validation). But the live measurement this doc set
  out to make found something more important: PM's `quickmerge.sh` Option-B path (`scripts/quickmerge.sh` ~line 1802,
  `--head "$BRANCH"` where `$BRANCH=live-defi-rollout`) opens its OWN separate PR straight to `main` with
  head=`live-defi-rollout` — a branch that moves every 20-90s under fleet commit velocity. That PR (`gh pr create --base
  main --head live-defi-rollout`, "Automated PR. Will auto-merge once quality gates pass.") is NOT frozen to a snapshot
  SHA the way the bot's PRs are — it just sits open and absorbs every subsequent commit via `pull_request: synchronize`,
  each one re-triggering a fresh `quality-gates-v2` run. **Measured directly on PR #1675** (opened 13:51:54Z): **22
  `quality-gates-v2` runs in ~45 minutes** (14 success, 7 cancelled, 1 in-flight at measurement time) — this is the SAME
  symptom the operator originally reported, and my earlier fix does not touch it, because it's a structurally different
  code path.

  The standing bot's own "bug#7 guard" already recognizes this exact shape (`head=live-defi-rollout, base=main`) as a
  stale land-mine and closes it on its next tick (~15-45min cadence) — so the churn window is bounded, not infinite, but
  every quickmerge ship that happens to find no such PR already open re-creates it, and the fleet ships constantly. This
  is the actual dominant churn source, not the bot mechanism I fixed earlier this session.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, quality-gates-v2, quickmerge, promote-bot, verification, root-cause-correction]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-07-27
author: unknown
parent_epic: infrastructure_master
priority: P1
source:
  operator request, 2026-07-27 — "ship a small change then confirm churn has improved"; the measurement itself surfaced
  this correction
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-27
locked_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/quickmerge.sh,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
  ]
resolved_by: 2026-08-05 verification (see Progress Log) — fix was already live, code + measurement confirm it
depends_on: []
---

# Promote-PR churn — corrected root cause

## What was measured

- PR #1675 (`IggyIkenna/unified-trading-pm`, opened `2026-07-27T13:51:54Z`, head=`live-defi-rollout`, base=`main`, body
  "Automated PR. Will auto-merge once quality gates pass." — quickmerge's own template, not the bot's) —
  `gh pr view 1675` confirms author `IggyIkenna` (PAT-driven, i.e. quickmerge itself, not the `uts-ci-poller` App bot).
- `gh run list --repo IggyIkenna/unified-trading-pm --workflow=quality-gates-v2.yml` filtered to
  `event=pull_request AND headBranch=live-defi-rollout AND createdAt >= 2026-07-27T13:51:54Z`: **22 runs** in the ~45
  minutes since the PR opened (14 `success`, 7 `cancelled`, 1 still running) — one fresh run per commit landing on
  `live-defi-rollout` from ANY concurrent slot/agent, not just PM-authored ones.
- Confirmed via `scripts/quickmerge.sh` (~lines 1797-1841): PM's "Option B" path (`PR_BASE=main` when
  `REPO_NAME=unified-trading-pm`) builds `gh pr create --base main --head "$BRANCH"` where `$BRANCH` is always
  `live-defi-rollout` for PM — there is no per-SHA freeze here, unlike the bot workflows. `gh pr create` silently fails
  (swallowed by `2>/dev/null`) once such a PR already exists, so subsequent quickmerge invocations just leave the
  existing one to auto-merge whenever CI happens to pass on whatever head SHA is current at that moment — this IS the
  mechanism, not a bug in error handling.
- Contrast: every OTHER (non-PM) repo's quickmerge path (`PR_BASE=staging`) does NOT open a PR itself for the normal
  case at all — it just lands on LDR and exits, relying entirely on the periodic `ldr-to-main-promote`-style drain bot
  (see `scripts/quickmerge.sh` ~line 1748-1751, "Landed on $BRANCH... Tier-C drain... promotes"). PM's Option-B path is
  the ONE place that still opens its own unfrozen, moving-head PR.

## Why this session's earlier fix didn't catch it

The earlier fix (this session, commit `48800b7ad`) patched `ldr-to-main-promote.yml` / `-fleet.yml`'s own
supersede-on-new-tip logic — that mechanism is real and does fire (its frozen-per-SHA-ref PRs, e.g. #1670/#1674, merge
cleanly), but it only becomes the ACTIVE promotion path when no live-branch-headed PR is already open. In practice,
since quickmerge.sh's Option-B path opens one on nearly every ship (whenever the bot hasn't already closed the prior
one), the fleet spends most of its time being drained through the churning path, not the fixed one. The earlier fix is
not wrong — it's just gating a mechanism that rarely gets the chance to be the bottleneck.

## Proposed fix (NOT executed — touches quickmerge.sh, the fleet's core shipping gatekeeper)

Make PM's Option-B path behave like every other repo's path already does: **land on `live-defi-rollout` and exit,
without quickmerge itself opening a direct PR to `main`.** Let the (now-fixed) `ldr-to-main-promote.yml` bot own 100% of
PM's main-ward promotion via its frozen-per-SHA-ref mechanism (bot ticks every ~15min; PM's LDR→main SLA comment already
targets ~30min). This removes the churning PR-open path entirely rather than papering over it, and is structurally
consistent with the rest of the script.

**Why this needs explicit confirmation before shipping**: `quickmerge.sh` gates every commit across the entire fleet.
This specific branch (Option-B, PM only) is narrower blast-radius than touching the shared staging-first path, but it
directly changes what "did my quickmerge succeed" looks like for PM specifically (no more immediate PR link in the
quickmerge output; the commit shows up on main only after the next bot tick, ~15-30min later instead of
near-immediately). That is a real behavior change worth the operator seeing before it ships, not something to silently
change mid-loop.

## Todos

- [x] ✅ [VERIFY] P1. Get operator confirmation, then remove quickmerge.sh's Option-B direct-PR-open step for PM
      (~scripts/quickmerge.sh lines 1784-1845) and replace with the same "land on LDR, exit, bot drains it" behavior
      every other repo already uses. Re-measure `quality-gates-v2` run count against a subsequent PM shipment window to
      confirm the churn actually drops once quickmerge stops opening this PR. **Already done** — read live
      `scripts/quickmerge.sh` today (2026-08-05): the PM branch (~line 2137-2150) now prints "Option B: lands on LDR
      trunk; ldr-to-main-promote.yml drains to main" and does NOT open a direct PR in the normal path — this IS the
      proposed fix, already shipped. My own quickmerge run this session (docs(plans) commit, unified-trading-pm) printed
      the confirming line live: "quickmerge stopped opening a competing direct PR here (churn fix, 2026-07-27)". So the
      fix landed the SAME DAY this issue was filed; only the issue bookkeeping was never closed.
- [x] ✅ [VERIFY] P2. Re-run this exact measurement (count `pull_request` `quality-gates-v2` runs on any open
      `head=live-defi-rollout, base=main` PR over a 45min window) after the fix ships, to get a genuine before/after
      pair instead of a single-sided measurement. **Done 2026-08-05**:
      `gh pr list --repo IggyIkenna/unified-trading-pm     --state open` shows zero PRs with
      `head=live-defi-rollout, base=main` (the churning shape) — the two open PRs target `base=live-defi-rollout`,
      unrelated. `gh run list --workflow=quality-gates-v2.yml --limit 20`: 0 of the last 20 runs are `pull_request`
      events on a `live-defi-rollout` head (vs. the 22-in-45min baseline this doc measured pre-fix). Churn confirmed
      gone.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — todo 1 explicitly requires operator
confirmation before removing quickmerge.sh's PM-specific Option-B direct-PR-open step (this doc's own "Why this needs
explicit confirmation before shipping" section: it changes the fleet's core shipping gatekeeper's observable behaviour
for PM). Parked as `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E6** and escalated
there as operator question 3. Todo 2 (the before/after churn re-measurement) is gated on todo 1 landing.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, valid — re-confirmed. Independently re-verified
the E6 citation is real (grepped the archived batch2 doc directly) and found a further independent re-confirmation at
`ci_satellite_ao_dispatch_batch4_2026_07_31.md` D4-11, still unruled as of today. Both open todos remain genuinely
operator-gated; no RECLASSIFY candidate here.

**context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).

## Progress Log

- **2026-08-05**: found while investigating a fleet CI-capacity question — the two "operator-gated" todos above were
  actually satisfied over a week ago. `scripts/quickmerge.sh`'s PM branch no longer opens a direct PR at all in the
  normal path (confirmed by reading it live + my own quickmerge run this session printing the exact "churn fix,
  2026-07-27" confirmation line) and a live measurement (0/20 recent `quality-gates-v2` runs on PM are `pull_request`
  events on a `live-defi-rollout` head, 0 open churning-shape PRs) confirms the churn is gone. **Neither
  na-eligibility-audit (2026-07-30, 2026-08-01) caught this — both re-confirmed "still operator-gated" without
  re-checking the live code/measurement, just the doc's own stale todo text.** Marking resolved; both todos closed with
  fresh evidence above. Worth a note for the audit process: KEEP-NA re-confirmations should spot-check the underlying
  claim, not just the todo's phrasing, especially past ~1 week old.
