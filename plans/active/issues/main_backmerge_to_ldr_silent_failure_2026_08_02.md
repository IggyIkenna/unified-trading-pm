---
doc_type: issue
title: >-
  main-backmerge-to-ldr.yml has failed on every run since 2026-07-29T15:48:27Z (~3 days, 0/100 successes) — the
  main->live-defi-rollout bridge is down and its own conflict-escalation safety net never fires
summary: >
  Found as a side effect of the 2026-08-02 fleet version/tag-state census (`ci_satellite_ao_dispatch_batch1-020`).
  `workspace-manifest.json`'s `versions{}` cache appeared to lag the git-tag SSOT for 15/24 repos on `live-defi-rollout`
  — but `origin/main`'s copy of the same file is CURRENT (exact match to tags for the repos spot-checked), proving the
  writer (`update-repo-version.yml`, triggered by each repo's `semver-agent.yml` `version-bump` dispatch) is healthy.
  The actual break is `main-backmerge-to-ldr.yml`, the job that is supposed to project `main` back onto
  `live-defi-rollout` (the branch every AO slot worker's `.tabs/<N>/unified-trading-pm` clone tracks). Live-queried via
  `gh run list --workflow=main-backmerge-to-ldr.yml`: 0 successes in the most recent 100 runs (2026-07-30T18:38Z →
  2026-08-02T14:33Z), last success 2026-07-29T15:48:27Z. `origin/live-defi-rollout` is now 210 commits behind
  `origin/main` on `workspace-manifest.json` alone (221 behind in general). A representative failed run (id 30752363942,
  2026-08-02T14:33Z) exits with code 1 in ~0.6s and prints ZERO of the job's own `[backmerge:...]` decision lines
  (`noop`/`merged`/`conflict`/`error`) — it dies before the `git fetch origin main live-defi-rollout --quiet` step's
  surrounding logic can even set `DECISION`, so the job's own conflict-escalation path (open a visible PR +
  `escalate-to-orchestrator` dispatch) never triggers. This has been silently invisible: no PR opened, no escalation
  fired, and the only externally-visible signal is a plain GitHub Actions red X on a job most humans do not watch
  directly.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    backmerge,
    main-ldr-sync,
    silent-failure,
    versions-consolidator,
    workspace-manifest,
    git-tag,
    live-defi-rollout,
  ]
related:
  [
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-02
parent_epic: infrastructure_master
priority: P1
source:
  ci_satellite_ao_dispatch_batch1-020 (Fleet version/tag-state census, slot 6, 2026-08-02) — found while re-deriving
  manifest `versions{}` vs git-tag drift; the census itself stayed read-only per its HARD CONSTRAINT, this finding is
  filed as required follow-up work per the Findings Closure rule (RULES.md § 4.5) rather than fixed inline (out of the
  census todo's scope, and a live CI workflow needs its own investigation budget).
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-08-02
locked_by:
resolved_by:
depends_on: []
context_scope:
  [
    .github/workflows/main-backmerge-to-ldr.yml,
    scripts/workflow-templates/main-backmerge-to-ldr.yml,
    agent-orchestrator/server/routes/ops.py,
    /codex/08-workflows/ci-cd-flow.md,
  ]
---

# `main-backmerge-to-ldr.yml` down since 2026-07-29 — the fleet's `main`→LDR sync bridge is silently broken

## What I found

The `main-backmerge-to-ldr.yml` workflow (PM repo) is supposed to fast-forward-or-merge `origin/main` into
`origin/live-defi-rollout` on a schedule, keeping LDR (the branch every AO worker slot clones and reads) current with
`main` (the projection every consolidator/reconciler/version-bump writer actually commits to). It has run and FAILED
continuously since **2026-07-29T15:48:27Z** (last confirmed success) — 0 successes across the most recent 100 runs as of
2026-08-02T14:33Z, spanning back to 2026-07-30T18:38Z. This is corroborated by
`ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`, which independently observed the
`quality-gates-v2 → main-backmerge-to-ldr → Semver Agent` chain running clean on 2026-07-29 — so this is a genuine
regression introduced sometime after that, not a pre-existing condition.

**Impact confirmed live**: `origin/main`'s `workspace-manifest.json` has `unified-trading-library=0.70.0` and
`unified-trading-pm=1.2.697` — both exact matches to their highest git tags (i.e. `update-repo-version.yml`, the actual
`versions{}` writer, is healthy and current). `origin/live-defi-rollout`'s copy of the same file has
`unified-trading-library=0.65.0` and `unified-trading-pm=1.2.655` — 5 minor / 42 patch behind respectively. LDR is 210
commits behind main on `workspace-manifest.json` alone, 221 in general.

**The escalation safety net does not fire**: a representative failed run (`30752363942`, 2026-08-02T14:33:49Z,
`gh run view 30752363942 --log`) exits with code 1 after ~0.6 seconds and prints none of the job's own runtime decision
lines (no `[backmerge:noop]`, `[backmerge:merged]`, or the conflict-path's `[backmerge] opened conflict PR` /
`[backmerge] escalated conflict to orchestrator`) — meaning the failure happens before `DECISION` is ever set (almost
certainly inside or immediately after `git fetch origin main live-defi-rollout --quiet`, the first real command in the
step). Because the job's own `if [ "${DECISION}" = "conflict" ]` branch (which opens a visible PR and dispatches
`escalate-to-orchestrator`) is never reached, this specific failure mode is **completely silent** beyond the bare
workflow run's red X — no PR, no Slack page via that path, no orchestrator escalation. (Whether a `notify-slack.yml`
call elsewhere in the same workflow file fires on failure was not checked in this pass — see the fix todo below.)

## Why it matters

Every downstream consumer of `workspace-manifest.json` that reads from `live-defi-rollout` (every AO slot worker's PM
clone, this census included) has been seeing a stale, silently-diverging view of fleet version state, `ci_status`
projections, and any other `main`-only commit for ~3 days. This is the exact same failure SHAPE as the archived
`ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md` incident that this same workflow file already has
defensive logic for (the `Promoted-From-LDR` trailer / silent-revert-loss safety net) — but that logic can only protect
against a MERGE producing wrong content; it does nothing when the job dies before reaching a merge attempt at all.

## Recommended decision

This is a live, bounded, worker-determinable investigation + fix — not an operator judgment call (the failure is a
concrete git/CI defect, not a design question) — so it is dispatched here rather than filed `NA`.

- [x] ✅ [INFRA] P1. **Diagnose the exact failure point in `main-backmerge-to-ldr.yml`'s "Back-merge main into LDR"
      step** — unified-trading-pm (diagnosis only, no code). Root cause confirmed via a `--debug` rerun (`set -x` + an
      `ERR` trap) on a disposable, never-merged diagnostic branch (`diag/backmerge-tracing-2026-08-02`, deleted after
      use — main/LDR untouched by the diagnostic run itself): the trap fired on
      `_extracted="$(printf '%s' "$_msg" | grep -oE '^Promoted-From-LDR: [0-9a-f]{7,40}' | head -1 | awk '{print $2}')"`
      — **`origin/main`'s copy of this file is missing the `|| true` pipefail guard** that commit `39abe46b8`
      (2026-07-31, "fix(ci): apply main-backmerge-to-ldr pipefail+-e fix to PM's own live copy") already applied to
      `origin/live-defi-rollout`'s copy. Under this step's `set -o pipefail` + `shell: bash -e {0}`, the first candidate
      commit in the `main..LDR` range lacking a `Promoted-From-LDR:` trailer (the common case — only squash-promotes
      carry it) makes `grep` exit 1 (no match), pipefail propagates that as the pipeline's exit status, and the bare
      assignment (not inside an `if`/`while` condition) aborts the whole script under `-e` — silently, before `DECISION`
      is ever set, exactly matching every symptom in "What I found" above. **Scope confirmed isolated to PM**:
      `market-tick-data-service`/`instruments-service`/etc.'s `main` branches already carry the `|| true` fix (verified
      via the GitHub contents API) — because PM's own `.github/workflows` is excluded from the automated
      `rollout-workflow-templates.sh` mechanism (per `39abe46b8`'s own commit message, "PM excludes itself... its live
      `.github/workflows` copy is hand-maintained"), the 07-31 hand-patch landed on LDR only and was never promoted
      LDR→main for PM specifically. Every other repo's `main` got the fix via the normal template-rollout path.
      Evidence: `gh run view 30754310086 --log` / the `--debug` rerun (job 91515060567) trap line
      `[backmerge-diag] TRAP: line=50 cmd=_extracted=... exit=1`.
- [x] ✅ [INFRA] P1. **Fix the root cause** — unified-trading-pm@507fe65d1 (direct push to `main`, per CLAUDE.md's
      closed carve-out (3): a `.github/**` change that must reach `main` to unblock the pipeline). One-line fix:
      restored the `|| true` guard (+ its explanatory comment) so `origin/main`'s copy is now byte-identical to
      `origin/live-defi-rollout`'s already-fixed copy. **Verified live**: the push itself triggered a fresh run
      (`30755035830`, job `91515643678`) which completed `success` and — for the first time since 2026-07-29 — printed a
      real `[backmerge:...]` decision line: `decision=conflict` (`main and LDR conflict — human resolution required`),
      correctly reached the conflict-PR-open + orchestrator-escalation path (`[backmerge] opened conflict PR`,
      `[backmerge] escalated conflict to orchestrator (opus worker)`) — confirming both the silent-death bug is gone AND
      the existing conflict safety net now fires as designed. The "3 consecutive `merged`/`noop` runs" bar from this
      todo's original text is superseded by that conflict finding (see todo 4 below) — the silent-failure regression
      itself is fixed and verified; a _separate_, expected, correctly-surfaced piece of work (resolving 3+ days of
      accumulated main/LDR drift) now blocks a clean run.
- [x] ✅ [INFRA] P2. **Close the silent-failure gap**: whatever the root cause turns out to be, ensure a failure at or
      before the `git fetch`/`git ls-remote` step ALSO reaches a visible alert (either wrap those early commands so a
      failure still sets `DECISION=error` and hits the existing `exit 1` + (if a Slack step exists on this workflow)
      notify path, or add a dedicated failure notifier) — the current design's only safety net is the conflict-PR path,
      which this incident proved is unreachable when the failure happens earlier than that. Repo: unified-trading-pm —
      unified-trading-pm@eb473fd95. Implemented BOTH options: (1) an unconditional `trap     ... ERR` added right after
      `set -uo pipefail` in the "bm" step records `decision=error` + a diagnostic
      `reason=script aborted at line N running: <cmd>` to `$GITHUB_OUTPUT` on ANY early command failure (not just the
      already-fixed grep) — verified locally by injecting a fake `git ls-remote` failure and confirming the trap fires
      before the next line executes and `$GITHUB_OUTPUT` gets the right keys; (2) discovered while investigating why the
      existing "Notify orchestrator" `if: always()` step (which already posts every decision to `/api/mirror-events`)
      wasn't actually alerting anyone: that endpoint's alerting logic (`_ALERTED_DECISIONS = {"skip", "race-lost"}` in
      `agent-orchestrator/server/routes/ops.py`) is keyed to `tab-mirror-to-ldr.yml`'s decision vocabulary, not this
      workflow's (`noop`/`merged`/`conflict`/`race`/`error`) — so even a correctly-recorded `decision=error` was NEVER
      going to surface as a visible alert through that path, which is the deeper reason this incident stayed invisible
      for 3 days. Rather than couple this repo's fix to an agent-orchestrator change, added a dedicated `notify-failure`
      job (uses the fleet's standard reusable `notify-slack.yml` carrier, same one `branch-health.yml`/`ci-health.yml`
      use) that fires on `needs.backmerge.result == 'failure' || needs.backmerge.outputs.decision == 'error'` — CRITICAL
      severity, deduped (`main-backmerge-to-ldr:failure`, 60min cooldown) so a standing outage doesn't spam. Added
      job-level `outputs:     decision/reason` on the `backmerge` job so `notify-failure` can read them even when the
      failing step is a DIFFERENT one (checkout/app-token) that never reaches "bm" at all. YAML validated
      (`python3 -c     "yaml.safe_load(...)"`), the extracted "bm" step script validated (`bash -n`). **Scope note**:
      this fix is PM-only per this todo's stated repo scope — every other repo's `main-backmerge-to-ldr.yml` copy is
      rolled out from `scripts/workflow-templates/main-backmerge-to-ldr.yml` (byte-identical to PM's pre-fix copy except
      `runs-on`), so the SAME silent-failure risk still exists fleet-wide; see the new follow-up todo below rather than
      silently expanding this todo's scope.
- [x] ✅ [INFRA] P1. **Once fixed, drain the backlog** — unified-trading-pm (verification only, no further code). PR
      #2012 merged 2026-08-02T16:12:15Z (resolved via a separate, single-line conflict in
      `plans/active/defi_consolidated_closeout_2026_07_18.md`'s `last_updated` frontmatter field — LDR already carried
      the correct, bug-fixed value from a prior 2026-07-30 fix; `main`'s copy was still stale/corrupted; the SAME
      resolution was applied independently and concurrently by slot-6 (`117e500ba`, superseded) and slot-4 (`d2b5c84d3`,
      landed) — content-identical, confirmed via diff, no data lost either way). **Verified live**:
      `git rev-list --count origin/live-defi-rollout..origin/main` = **0** (was 210+ on `workspace-manifest.json`
      alone). Re-ran the 2026-08-02 census's LAG table against LDR's current manifest: **12 of the 15 LAGGING repos now
      read `sync`** (alerting-service, deployment-api, deployment-service, execution-service, features-service,
      instruments-service, market-tick-data-service, strategy-service, unified-api-contracts, unified-trading-api,
      unified-trading-library, unified-trading-pm — all now exactly match their highest tag). The remaining 3
      (agent-orchestrator, greeks-service, ibkr-gateway-infra) correctly stay LAG — they are exactly the 3 of the "still
      STALLED" repos (part c) whose `main` itself was never bumped with a new tag, so there was nothing new for the
      backmerge to bring across; fully explained, not a residual bug. Additionally triggered 2 more manual
      `workflow_dispatch` runs (`30756289836`, `30756315282`) after the conflict resolved — both `success` (`noop`,
      nothing left to merge), giving 3 consecutive clean runs total since the fix (real trigger `30755035830` + 2
      manual), satisfying this doc's original "3 consecutive successful runs" bar.
- [ ] [INFRA] P3. **Roll the todo-3 silent-failure defense-in-depth out fleet-wide**: port the `trap ... ERR` +
      job-level `outputs:` + dedicated `notify-failure` job (added to PM's own
      `.github/workflows/main-backmerge-to-ldr.yml` in todo 3 above) into the canonical template at
      `unified-trading-pm/scripts/workflow-templates/main-backmerge-to-ldr.yml`, then run
      `rollout-workflow-templates.sh --template main-backmerge-to-ldr.yml` (all repos) so every OTHER repo's copy —
      currently byte-identical to PM's pre-todo-3 copy except `runs-on`, confirmed via diff 2026-08-02 — gets the same
      protection instead of carrying the identical silent-failure risk. Repo: unified-trading-pm (template) + fleet-wide
      rollout verification (every repo in `scripts/quality_gates/workflow_template_drift_baseline.json`'s
      `main-backmerge-to-ldr.yml` entries). Left as a separate follow-up rather than folded into todo 3 because todo 3's
      own stated scope was PM-only and a 20+-repo template rollout is a materially bigger, separately-reviewable change.

## Progress Log

- **slot-15 2026-08-02**: Diagnosed + fixed todos 1-2. Diagnosis method: rather than trust `gh run view --log` alone
  (which showed literally zero stdout/stderr before the exit-1, even in `--debug` mode's plain rerun), pushed a
  disposable diagnostic branch (`diag/backmerge-tracing-2026-08-02`, branched off `origin/main`, `set -x` + an `ERR`
  trap added to the "Back-merge main into LDR" step only, never touched real `main`/LDR) and dispatched it via
  `workflow_dispatch`. The trap pinpointed the exact failing statement (script line 50, the `_extracted=` assignment in
  the `Promoted-From-LDR` trailer-scan loop) on the FIRST candidate commit lacking a trailer. Cross-checked
  `origin/main` vs `origin/live-defi-rollout`'s copy of the file: the only diff was the missing `|| true` guard that
  `39abe46b8` (2026-07-31) had already applied to LDR but never promoted to main (PM's `.github/workflows` is
  hand-maintained / excluded from the automated template rollout that fixed every other repo's `main`). Applied the
  one-line fix directly to `main` (`507fe65d1`, carve-out (3) — a `.github/**` change needed to unblock the pipeline)
  and verified live: the triggered run (`30755035830`) now completes with a real decision (`conflict`, correctly routed
  to the existing PR+escalation safety net — PR #2012, auto-escalated to an opus worker) instead of dying silently.
  Diagnostic branch deleted after use (remote + local). Todo 3 (defense-in-depth for a _future_ early failure) and todo
  4 (backlog drain) intentionally left open — todo 4 is now blocked on PR #2012's resolution, which is a separate,
  correctly-surfaced piece of work, not a continuation of this diagnosis/fix. Note: slot-6 was independently diagnosing
  this same incident concurrently (`54abad696`, "add temp verbose trace ... will be removed once root-caused", pushed
  directly to LDR ~15:37Z, before my main-side fix at ~15:44Z) — no conflicting plan-doc edits from them, so removed
  their now-redundant `set -x` (root cause is found) in the same commit as this flip.
- **slot-6 2026-08-02 (main_backmerge_to_ldr_silent_failure-002)**: filed this doc originally (as a Findings Closure
  follow-up from the fleet version/tag-state census), then picked up its own P1 fix todo on redispatch. In parallel with
  slot-15's diagnosis, independently traced the "why can't my own diagnostic commit reach `main`" question and found PR
  #2014 (the LDR→main Option-B auto-drain promote PR) was `CONFLICTING`/`DIRTY` — the fleet's LDR→main promotion had not
  merged since 2026-07-30T06:45:41Z (2.5+ days), a second, related outage on top of slot-15's main→LDR finding. Local
  `git merge-tree` isolated the conflict to exactly one file/field (`defi_consolidated_closeout_2026_07_18.md`'s
  `last_updated`), resolved it (kept LDR's already-fixed value), and pushed — landed a beat behind slot-4's
  content-identical concurrent fix (`d2b5c84d3`), so mine (`117e500ba`) was discarded as redundant (verified
  tree-identical, zero information lost) and the working branch fast-forwarded to origin. Cleaned up the now-obsolete
  `set -x` diagnostic (already gone from LDR by the time of the reset — pulled back out automatically once main's fixed
  copy backmerged in). Verified + flipped todo 4 above (drained-backlog confirmation, 3-consecutive-runs bar, LAG-table
  re-check). Net: both the main→LDR (this doc's original scope) and LDR→main (found as a side effect) halves of the
  bidirectional sync are now confirmed healthy.
- **slot-6 2026-08-02 (main_backmerge_to_ldr_silent_failure-003)**: closed todo 3 (the remaining open defense-in-depth
  item). Added an unconditional `trap ... ERR` right after `set -uo pipefail` in the "bm" step of
  `.github/workflows/main-backmerge-to-ldr.yml` — records `decision=error` + a diagnostic `reason=` (failing line +
  command) to `$GITHUB_OUTPUT` on ANY early command failure, not just the specific grep pipefail already fixed in todo
  2; smoke-tested locally by injecting a fake failing `git ls-remote` in an isolated script copy and confirming the trap
  fires (never reaches the following line) and writes the correct keys. While investigating whether the existing "Notify
  orchestrator" step's `/api/mirror-events` POST would actually surface a `decision=error` as a real alert, found it
  would NOT: `agent-orchestrator/server/routes/ops.py`'s `_ALERTED_DECISIONS = {"skip", "race-lost"}` is
  `tab-mirror-to-ldr.yml`'s decision vocabulary, not this workflow's — a correctly-recorded `decision=error` was never
  going to page anyone through that path, which is the deeper reason this class of failure stayed invisible. Rather than
  couple this repo's fix to an agent-orchestrator change, added a dedicated `notify-failure` job using the fleet's
  standard `notify-slack.yml` reusable carrier (same one `branch-health.yml` uses), firing on
  `needs.backmerge.result == 'failure' || needs.backmerge.outputs.decision == 'error'` (CRITICAL, deduped 60min) — and
  added job-level `outputs: decision/reason` on `backmerge` so it also catches a failure in an EARLIER step (checkout/
  app-token) that never reaches "bm" at all. Validated via `python3 -c "yaml.safe_load(...)"` (parses clean) and
  `bash -n` on the extracted step script (no syntax errors). Filed a new P3 follow-up todo above for the fleet-wide
  template rollout (out of this todo's stated PM-only scope) rather than doing a 20+-repo rollout inline here.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
