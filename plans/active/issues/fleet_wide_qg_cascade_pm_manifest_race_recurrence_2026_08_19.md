---
doc_type: issue
title: "Fleet-wide QG cascade recurred (7 repos, 2026-08-18 ~20:33-21:14 UTC) — single ff-only-pull retry was insufficient; hardened to force-reset + 2 retries"
summary: >-
  Operator asked (via /ci-reconcile) whether the 9 #ci-failures CRITICAL alerts from the 2026-08-18 evening window
  were a symptom of agents skipping quality-gates.sh before push. Root-caused: they were NOT — every affected repo's
  own commit passed cleanly on re-verification. This is a RECURRENCE of the already-archived
  fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18 incident (same "Production readiness
  validators FAILED" signature via the shared PM-corpus-validation step every repo's QG "checks" slice runs), hitting
  7 repos (deployment-service, ml-service, trading-agent-service, strategy-service, instruments-service,
  unified-trading-library, market-tick-data-service) in a ~20:33-21:14 UTC window — several hours after the first
  incident's fix (unified-trading-pm@176ff63dab, a single re-pull + 5s + one retry) had already landed and was live.
  New evidence this session: the EXACT PM commit that was live-defi-rollout HEAD at both confirmed failure moments
  (304f95484, tested via git-worktree-pinned re-run of the identical CI-invoked script) validates 100% clean in
  isolation — refuting "PM content was actually invalid" as the mechanism for THIS occurrence and pointing instead at
  a stale/dirty local PM clone surviving between jobs on the self-hosted `[self-hosted, glue]` runners (workspace
  reuse), which a soft `git pull --ff-only` does not reliably correct. Hardened the retry in both
  scripts/quality-gates-base/base-service.sh and base-library.sh: force `fetch` + `reset --hard` + `clean -fdx`
  (instead of `pull --ff-only`) with up to 2 retries (5s, 10s backoff) instead of 1. All 9 originally-alerted repos
  independently re-verified green on current live-defi-rollout HEAD before and after this fix.
status: open # fix shipped + verified same commit; sole remaining todo is an optional operator-owned confirmation
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    deployment-service,
    ml-service,
    trading-agent-service,
    strategy-service,
    instruments-service,
    unified-trading-library,
    market-tick-data-service,
    alerting-service,
  ]
scope: [engineer, admin]
tags:
  [ci-reconcile, quality-gates-v2, fleet-wide, single-point-of-failure, self-hosted-runners, workspace-manifest]
related:
  [/plans/active/ci_consolidated_closeout_2026_07_25.md, /codex/08-workflows/ci-cd-flow.md, /codex/15-runbooks/ci-daily-health.md]
created: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
source: >-
  /ci-reconcile interactive investigation, 2026-08-19 — operator pasted the 9 raw #ci-failures CRITICAL alerts from
  the prior evening and asked why they happened if agents run quality-gates.sh + quickmerge before every push;
  root-caused via direct gh run/job/log inspection + git-worktree-pinned historical-tree replay across all 9 repos.
resolved_by: >-
  force-reset retry hardening in base-service.sh + base-library.sh, shipped in this same commit — see Finding 2 for
  why the original 176ff63dab fix under-covered this recurrence, and the Open Question for what remains unconfirmed.
locked_by:
depends_on: []
---

# Fleet-wide QG cascade recurrence — none of it was agents skipping QG

## What I found

### Finding 1 — every alerted commit's OWN code was clean; this was never an agent-discipline problem

For all 9 alerted `sha`s, current `live-defi-rollout` HEAD is 0 ahead/0 behind origin and every repo's latest
`quality-gates-v2` run is green. Two of the 9 alerts (deployment-service `b7fb1584`, unified-trading-pm `4c9549a1`)
were ordinary agent commits with no relation to each other; the other 7 were `uts-backmerge-bot` merge commits
(`main` → `_backmerge` → LDR), all landing within a ~20-minute window. **No agent shipped without running QG** — the
failing shas, when manually re-dispatched later on identical code, passed (confirmed for ml-service,
trading-agent-service, market-tick-data-service, unified-trading-library, deployment-service — each shows both a
`failure` and a later `success` run against the exact same `head_sha`).

### Finding 2 — same shared-PM-validator single point of failure as the archived incident, but the existing fix under-covered it

6 of the 7 backmerge-window failures (deployment-service, ml-service, trading-agent-service, strategy-service,
instruments-service, unified-trading-library) share the IDENTICAL failure signature already documented in
`fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md` Finding 1: job "QG slice (checks)" →
step "Run quality gates (leg checks)" → `[6/6] PRODUCTION READINESS VALIDATORS` → `❌ Production readiness
validators FAILED (persisted after re-pull + retry)`. (market-tick-data-service's failure was a distinct "Set up
job" infra hiccup, unrelated to this class.)

The `"(persisted after re-pull + retry)"` phrasing is literally the 2026-08-18 fix's own log line — meaning the fix
WAS live and DID run its one retry, and STILL failed for these repos. This is a real gap in the first fix, not a
new/different bug: a single `sleep 5` + one retry was not enough to survive this window.

**New evidence — the "bad PM content" theory does not hold for this occurrence**: bisected the exact PM commit that
was `live-defi-rollout` HEAD at both confirmed failure timestamps (instruments-service 21:13:20Z, strategy-service
21:14:15Z — both resolve to the same commit, `304f95484`, and confirmed via `--since`/`--until` that no other PM
commit landed in the surrounding 6-minute window). Checked out that exact commit in an isolated `git worktree` and
ran the identical CI-invoked script (`codex/scripts/run-all-validators.sh --asset-group all --failed-only`) against
it directly: **clean pass, exit 0** — `workspace-manifest.json valid`, `No broken links in plans/active/*.md`, both
checklist items OK. So the commit that should have been live at the failure moment was not actually broken, which
means the failure mode this time was NOT "PM's tree was transiently invalid content-wise" (the archived doc's
Finding 1 mechanism) — something else caused the retry's `git pull --ff-only` to still leave the validator seeing an
invalid state even though the true upstream tree was fine.

**Working hypothesis (not independently confirmed — see Open Question)**: the affected repos run on dedicated
`[self-hosted, glue]` runners (`runs-on: [self-hosted, glue]`, confirmed in strategy-service's
`quality-gates-v2.yml`), which — unlike ephemeral `ubuntu-latest` runners — commonly reuse a persistent `_work`
directory across successive job runs. `git pull --ff-only` will silently no-op (without erroring) if the local PM
clone has any dirty/untracked state left over from a prior job on the same runner instance, which would explain a
retry that "succeeds" (pull exits 0) yet still validates against a stale tree — exactly matching the observed
"persisted after re-pull + retry" outcome on content that tests clean in isolation.

## Fix shipped

Hardened the retry in `scripts/quality-gates-base/base-service.sh` and `base-library.sh` (identical block, both
files, the same two files the 2026-08-18 fix touched):

1. **Force-resync instead of soft pull**: `git fetch` + `git reset --hard origin/live-defi-rollout` + `git clean
   -fdx` instead of `git pull --ff-only`. Eliminates the entire "stale/dirty local clone silently not corrected by
   a fast-forward-only pull" failure class regardless of which exact mechanism caused it — PM's CI-side clone is a
   disposable dependency checkout, never a place with legitimate local state worth preserving, so a hard reset is
   strictly safe here.
2. **2 retries instead of 1**, with backoff (5s, 10s) instead of a flat 5s — gives a longer window to clear a
   sustained high-churn period (this incident's surrounding PM commit activity ran near-continuously for close to 2
   hours, not the tight ~2-minute burst the first incident's fix was sized for).
3. Verified `bash -n` syntax-clean on both files; behavior is otherwise identical (still hard-fails after
   exhausting retries — this does not weaken detection of a genuinely, persistently broken PM corpus).

All 9 originally-alerted repos' current `live-defi-rollout` HEAD reconfirmed green (fresh `quality-gates-v2` runs,
all `conclusion: success`) both before and after this fix — nothing was left red; this fix targets recurrence
prevention, not an active failure.

## Open Question — runner-workspace-reuse hypothesis is plausible but NOT independently confirmed

I do not have access to the self-hosted runner hosts' filesystem/job history from this dev checkout, so I could not
directly confirm the "stale local PM clone reused across jobs" mechanism — only that (a) the content-race
explanation is ruled out for this occurrence, and (b) the runners are self-hosted with workspace-reuse-prone
`_work` semantics, which is consistent with the observed symptom. **The force-reset+clean fix is safe and correct
regardless of which exact mechanism is true**, so it ships without waiting on this confirmation. If this recurs a
THIRD time with the hardened retry in place, that would be strong evidence the mechanism is something else entirely
(e.g., a genuine network-level clone flake, or GH API eventual-consistency on the self-hosted runner's outbound
fetch) and warrants direct runner-host log access to resolve definitively.

## Todos

- [ ] [OPERATOR] P3. If runner-host SSH/log access is available, confirm whether `_work/<repo>/unified-trading-pm`
      on the `glue-1` self-hosted runner instances is reused (not freshly cloned) across successive job runs — this
      would directly confirm or refute the workspace-reuse hypothesis in the Open Question above, independent of
      whether the fix already shipped is sufficient.
- [x] ✅ [SCRIPT] P1. Root-cause all 9 alerted #ci-failures CRITICALs. DONE — see Finding 1: none were agent-QG
      discipline failures; all 9 repos' current HEAD confirmed green.
- [x] ✅ [SCRIPT] P1. Identify why the already-shipped 2026-08-18 retry fix didn't prevent this recurrence. DONE —
      see Finding 2: single retry + soft `pull --ff-only` was insufficient for a sustained high-churn window; the
      exact historical PM content tested clean in isolation, ruling out a content-race explanation for this
      occurrence specifically.
- [x] ✅ [SCRIPT] P1. Harden the retry. DONE — force-reset (`fetch`+`reset --hard`+`clean -fdx`) + 2 retries (5s,
      10s) shipped in both base-service.sh and base-library.sh, `bash -n` clean.
