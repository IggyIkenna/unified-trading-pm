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
  **CORRECTION (found after initial write-up)**: this is the SAME incident (identical 9 shas) already independently
  investigated and archived same-day as pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18 — a
  process gap on my part, this doc's investigation should have started with a plans/active + issues/ grep and found
  it first. That doc has direct raw-log evidence (2 of 9 repos) of a genuinely persistent (~20-40min) plans/active/*.md
  dangling-link break during concurrent /plan-reconcile sweeps, self-healed by PM's own automation, no code fix
  judged warranted at the time. My own evidence (the exact PM commit live at 2 OTHER repos' specific failure
  timestamps tests 100% clean in isolation) does not contradict that — it's consistent with an intermittent/flapping
  corpus validity across the ~20-40min window as multiple concurrent sweeps each fixed their own dangling refs at
  different times. The self-hosted-runner-workspace-staleness idea below is a secondary, unconfirmed hypothesis, not
  the primary explanation. Hardened the retry anyway in scripts/quality-gates-base/base-service.sh and
  base-library.sh: force `fetch` + `reset --hard` + `clean -fdx` (instead of `pull --ff-only`) with up to 2 retries
  (5s, 10s backoff) instead of 1 — safe and strictly better regardless of mechanism, but honestly it does NOT span
  the actual ~20-40min incident window (that's a materially bigger ask the archived doc explicitly reasoned isn't
  worth it fleet-wide). Also reordered `[6/6] PRODUCTION READINESS VALIDATORS` to run FIRST (`[0.5/6]`, right after
  basic toolchain sanity) instead of last, in both files — a pure fail-fast win independent of root cause: a doomed
  run now fails in seconds instead of after paying for the repo's own lint/type-check/test/codex-compliance steps.
  All 9 originally-alerted repos independently re-verified green on current live-defi-rollout HEAD before and after
  these changes.
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
context_scope:
  [
    /plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md,
    /plans/archive/2026_08/issues/pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18.md,
    scripts/quality-gates-base/base-service.sh,
    scripts/quality-gates-base/base-library.sh,
    /codex/08-workflows/ci-cd-flow.md,
  ]
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
  force-reset retry hardening + [6/6]->[0.5/6] fail-fast reorder in base-service.sh + base-library.sh — see Finding 2
  for why the original 176ff63dab fix under-covered this recurrence, and the Correction section for what this
  investigation got right vs. what a same-day archived doc already established more directly.
locked_by:
depends_on: []
archive_exempt: true
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
4. **Reordered to fail-fast**: moved the `[6/6] PRODUCTION READINESS VALIDATORS` section to run FIRST as `[0.5/6]`
   (right after `[0/6] ENVIRONMENT`'s toolchain sanity checks, before the repo's own `[1/6]` AUTO-FIX / `[2/6]` LINT
   / `[3/6]` TESTS / `[4/6]` TYPE CHECK / `[5/6]` CODEX COMPLIANCE). It only needs PM's already-cloned checkout (the
   CALLER workflow's earlier "Clone unified-trading-pm and dependencies" step, not anything steps 1-5 produce), so
   there was never an architectural reason it had to run last — that ordering looks like the section was originally
   just appended to the end of an already-long script. This is a pure fail-fast win, orthogonal to root cause: on
   ANY of the failure classes discussed here (instant manifest-write race, sustained dangling-link break, or
   runner-workspace staleness), a doomed run now fails in seconds instead of after paying for the repo's own
   lint/type-check/test/codex-compliance work first. Kept the `[6/6]`-derived phrase in the section's prose comment
   (not the `log_section` label, which now reads `[0.5/6]`) so existing docs/greps for the old identifier still
   resolve to the right place.

All 9 originally-alerted repos' current `live-defi-rollout` HEAD reconfirmed green (fresh `quality-gates-v2` runs,
all `conclusion: success`) both before and after this fix — nothing was left red; this fix targets recurrence
prevention, not an active failure.

## Correction — this IS pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18, re-investigated

Found only after Findings 1-2 and the fix above were already written: a same-day archived doc,
`pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18` (status: resolved, self-healed), already
covers this EXACT incident — identical 9 repos, identical shas. It should have been the first thing this
investigation found (a `plans/active/` + `issues/` grep before starting, per the workspace's own pre-task
plan-conflict-check rule) — the miss cost duplicated investigation, though it also produced genuinely additional
evidence (below), so the pass wasn't wasted.

**What that doc establishes that this one didn't originally know**: direct raw failure logs for 2 of the 9 repos
(alerting-service, unified-trading-pm) show `"Already up to date."` on the retry's `git pull` — meaning there was
nothing new to fetch, the bad content was already the committed HEAD, and it stayed bad long enough (~20-40 minutes,
self-healed only once PM's own later `/plan-reconcile` commits landed) that every one of the 9 repos' independent CI
runs across that window hit it. That's a genuinely persistent content break in `plans/active/*.md` (the dangling-link
sub-check specifically, not `workspace-manifest.json`, which passed both times in their captured log), not an
instant race — and per that doc's own explicit reasoning, no retry window shy of 20-40 minutes could ever have
caught it, which is not a viable trade for every one of the fleet's daily QG runs.

**How this reconciles with my own "clean at 304f95484" finding**: that doc didn't pin down the exact commit/link
that broke (their words: "not pinned down, self-heal confirmed by outcome, not by diff") — it confirms the WINDOW
was bad via captured logs from 2 specific repos, not that every single commit inside the window was bad. My
bisection covered 2 DIFFERENT repos' specific moments (instruments-service 21:13:20Z, strategy-service 21:14:15Z)
and found a clean commit there. Given the stated root cause — several independent concurrent `/plan-reconcile`
sweeps each fixing only their OWN dangling refs in their own commits — the corpus's overall validity plausibly
flapped commit-to-commit across the window rather than being uniformly broken throughout, so both findings can be
true simultaneously: genuinely broken for some repos' moments, clean for others'. The runner-workspace-staleness
idea remains a live but now clearly secondary, unconfirmed hypothesis for the moments that DID test clean — not the
primary explanation for the incident as a whole.

**Net effect on what's shipped**: the retry + force-reset hardening and the fail-fast reordering both stand as safe,
independently-justified improvements (see Fix shipped items 1-4) — but neither one, honestly, would have prevented
this specific incident's actual ~20-40min outage. That gap is the ALREADY-TRACKED P3 follow-up in the archived
doc's own "Follow-ups" section (pin repos' validator against a last-known-green PM sha instead of live HEAD,
deferred until a third occurrence) — this investigation is that doc's "second data point" being re-examined with
more forensic depth, not a new third occurrence, so that threshold is not yet met.

## Todos

- **[OPERATOR] P3. CANCELLED — SUPERSEDED 2026-08-22 (D82 ruling: skip — low-value confirmation the doc itself
  treats as optional; the incident's primary mechanism — a genuinely persistent dangling-link break, not runner
  staleness — is already understood for at least 2 of 9 repos).**
- [x] ✅ [SCRIPT] P1. Root-cause all 9 alerted #ci-failures CRITICALs. DONE — see Finding 1: none were agent-QG
      discipline failures; all 9 repos' current HEAD confirmed green.
- [x] ✅ [SCRIPT] P1. Identify why the already-shipped 2026-08-18 retry fix didn't prevent this recurrence. DONE —
      see Finding 2 + Correction: single retry + soft `pull --ff-only` was insufficient; a same-day archived doc
      (found after the fact) already established the primary mechanism as a genuinely persistent (~20-40min)
      dangling-link break, not an instant race — no retry width shipped here claims to span that.
- [x] ✅ [SCRIPT] P1. Harden the retry. DONE — force-reset (`fetch`+`reset --hard`+`clean -fdx`) + 2 retries (5s,
      10s) shipped in both base-service.sh and base-library.sh, `bash -n` clean.
- [x] ✅ [SCRIPT] P2. Reorder `[6/6]` to run first for fail-fast (operator-requested follow-up, same session). DONE
      — relabeled `[0.5/6]`, moved to right after `[0/6] ENVIRONMENT` in both files, `bash -n` clean.

## Progress Log

- **context-scout 2026-08-19**: populated/refreshed context_scope (5 entries).
- **2026-08-19 (self-correction)**: found `pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18`
  (archived, same-day, identical 9 shas) only after Findings 1-2 and the initial fix were already written — should
  have grepped `plans/active/` + `issues/` before starting per the workspace's pre-task plan-conflict-check rule.
  Added the Correction section reconciling both docs' evidence; the shipped retry-hardening + reorder stand as safe
  improvements but neither claims to have prevented the actual ~20-40min incident.
- **context-scout 2026-08-20**: re-verified context_scope (5 entries), unchanged.

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid. Sole open todo (`[OPERATOR] P3`, confirm
whether the `glue-1` self-hosted runner's `_work/<repo>/unified-trading-pm` checkout is reused across successive
job runs) explicitly requires runner-host SSH/log access — a live-infra check outside a worker's normal reach, and
the doc's own text already downgrades it to secondary priority (the incident's primary mechanism — a genuinely
persistent dangling-link break, not runner staleness — is understood for at least 2 of 9 repos). No `assigned_vm`
change.
- **2026-08-22 — ruling D82 (glue-1 checkout-reuse check)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Skip — low-value confirmation the doc itself treats as optional. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-22 (archive-exemption note)**: this D82 retag closed the doc's last open checkbox (0 open todos remain).
  Marked `archive_exempt: true` rather than archiving — out of scope for this ruling-sweep pass per the parent task's
  explicit "do not archive any doc" instruction; a future archive-candidates pass should run the normal 6-step ritual
  instead.
