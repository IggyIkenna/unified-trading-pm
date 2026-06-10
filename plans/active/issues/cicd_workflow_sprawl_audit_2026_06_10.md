---
title:
  "CI/CD GitHub-Actions workflow sprawl audit — dead/duplicate/band-aid workflows fleet-wide (verified across 25 repos)"
created: 2026-06-10
source:
  - codex/08-workflows/ci-cd-flow.md
  - scripts/workflow-templates/
  - "fleet-wide dispatch-graph verification, slot-4 @ LDR 2026-06-10 (PM a71add30a)"
locked_by: live-defi-rollout
status: active
priority: P1
---

# CI/CD workflow sprawl audit — what can be removed / merged

> **Trigger:** the CI/CD pipeline grew organically — agents added new workflows to patch edge cases in existing ones,
> which created their own edge cases. We now carry ~45 orchestrator workflows in PM (plus ~10 templated to all 25
> repos). This doc catalogues what is genuinely **dead / duplicate / band-aid** and what only _looked_ dead under a
> narrow single-repo grep but is live fleet-wide.

## Methodology (so the recommendations are trustworthy)

Verified on **slot-4, all 25 repos freshly FF-pulled to `origin/live-defi-rollout`** (PM `aa48b981a → a71add30a`),
2026-06-10. Every "dead emitter / no consumer / no caller" claim was re-checked **across all 25 repos'
`.github/workflows/` AND `scripts/`** (not just PM), because:

- repository*dispatch **emitters** routinely live in a \_different* repo (e.g. every service's `semver-agent.yml` emits
  `version-bump` / `schema-changed`), or in Python/bash under `scripts/`, or in a **propagation template** not yet
  rolled out.
- the real dispatch syntax is `{\"event_type\": \"<ev>\", \"client_payload\": …}` (escaped quotes) — a naive
  `event_type=<ev>` grep silently misses every emitter. The corrected matcher was validated against known-live controls
  (`version-bump` → lights up 25 `semver-agent.yml`; `qg-passed` → 25 `quality-gates-v2.yml`; `tier-ab-green` →
  `ci-status-update.yml`) before trusting any "0 hits = dead" result.
- **Variable-indirected emits are a blind spot** for an `event_type=<ev>` grep: e.g. `full-workspace-sit.yml` sets
  `EVENT="sit-passed"` then dispatches `-f event_type="$EVENT"`. So every "dead" conclusion was re-confirmed against the
  **bare literal string in any context** — only a type whose _sole_ fleet-wide occurrence is the consumer's own
  `types:[…]` line (no assignment, no dispatch) is treated as dead. (`sit-passed` initially looked dead under the
  `event_type=` grep and is in fact LIVE — it is excluded from the dead list below.)
- **Completeness sweep, not just the flagged subset:** every `workflow_call` callee in PM was checked for a caller (only
  `contract-replay` + `request-major-bump-reusable` have zero), and every `repository_dispatch` consumer type was
  checked for an emitter. No dead callee/type beyond those listed below was found.
- **Branch caveat closed:** workflows fire from the **default branch (`main`)**, not LDR. PM `main` and
  `live-defi-rollout` are byte-identical under `.github/workflows/` (verified
  `git diff origin/main origin/live-defi-rollout`), so the LDR-clone analysis holds for the branch that actually runs.

**Template footprint** (edit via `scripts/workflow-templates/` SSOT + `rollout-workflow-templates.sh`, then commit
per-repo fleet-wide — never hand-edit one repo's copy):

- **Templated (×17–25 repos):** `tab-mirror-to-ldr`, `major-bump-issue-handler`, `request-major-bump`,
  `main-backmerge-to-ldr`, `staging-backmerge-to-ldr`, `semver-agent`, `quality-gates-v2`, `staging-lock-check`,
  `update-dependency-version`.
- **PM-hub-only (×1 — safe to edit in place):** everything else flagged below.

---

## Independent re-verification (slot-2 @ LDR, 2026-06-10, PM `bbf89da05`)

A second reviewer re-ran every claim below against all 25 freshly-FF'd worktrees. **Findings: the audit is accurate.**
Specifically re-confirmed: (A) all four deletes are genuinely dead — `contract-drift-record` even pings Slack nightly
via 3 echo stubs + `notify-slack.yml`; (B1) `major-bump-approval.yml` does a *full* staging version bump + dispatch
(not just a label) so the double-run is real; (D) the `ldr-to-staging` references in `ci-status-update`/`quickmerge.sh`/
`tier_c_promotion_gate.py` are **filename mentions in comments, not emitters** — the prune holds; (E) the
`publish-package` emitter exists only as the propagation template (`event_type: "publish-package"` line 49) with no live
emitter; (F) `tab-mirror` `*/15` cron is live and even **auto-rebases + force-pushes diverged tabs** and POSTs an
orchestrator webhook every run (the audit if anything *understates* it). **Completeness re-checked:** the 7 consumer
types the audit did not flag (`cascade-qg-trigger`, `ci-status-update`, `merge-conflict-detected`, `promotion-conflict`,
`sit-lock`, `staging-changed`, `staging-validated`) each have a live emitter — no additional dead type exists.

**One correction — B2 severity is downgraded** (see B2 below): both backmerge workflows push **FF-only with 5× retry +
never-force**, so the divergent concurrency groups cannot actually clobber LDR. B2 is a *contract violation + avoidable
retry churn*, not the data-correctness defect the original "race LDR writes" wording implied. The trivial fix still
applies. Everything else stands as written.

## What I found

### A. Confirmed DEAD — safe to delete (PM-only, verified 0 emitters/callers fleet-wide)

| Workflow                            | Evidence (fleet-wide)                                                                                                              | Note                                                                                                                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `downstream-fix-agent.yml` (851 ln) | `downstream-fix-needed` dispatch: **0 emitters** in any repo's workflows OR scripts. Reachable only by manual `workflow_dispatch`. | Also still burns pay-per-call `ANTHROPIC_API_KEY` — contradicts the 2026-06-03 VM-worker pivot. The SIT `test_cascade_flow.py` asserting it is wired tests a never-fired path. |
| `contract-replay.yml`               | `workflow_call` callee with **0 `uses:` callers**; body is `echo`-only stub.                                                       | Superseded by `cassette-drift-check.yml`.                                                                                                                                      |
| `contract-drift-record.yml`         | `echo`-only stub (3 stub steps); **same `0 2 * * *` cron** as the implemented `cassette-drift-check.yml`.                          | Original skeleton; never implemented.                                                                                                                                          |
| `request-major-bump-reusable.yml`   | byte-identical to `request-major-bump.yml` but `workflow_call`; **0 `uses:` callers**.                                             | A reusable split that was never wired.                                                                                                                                         |

### B. Active BUGS (not just sprawl)

1. **Duplicate `/approve` handlers double-execute MAJOR bumps — PM-scoped.** `major-bump-issue-handler.yml` AND
   `major-bump-approval.yml` have the **identical** trigger (`issue_comment:[created]`) and gate
   (`contains(labels,'major-bump-pending') && startsWith(comment,'/approve'|'/reject')`). Both fire on the same comment
   → two version bumps, two `version-bump` dispatches, two close attempts. Their concurrency groups differ
   (`workflow-ref` vs `manifest-update`) so they do **not** serialize → genuine double-run. **Scope correction:**
   `major-bump-approval.yml` is **PM-only**; `major-bump-issue-handler.yml` is templated to all 25. So the
   double-execution happens **only in PM** — every service repo has just the one handler and is fine. **Latent but real
   (low-frequency / high-impact):** it only fires on the rare human `/approve` of a MAJOR-bump issue (a 1.0.0-graduation
   class event), but both handlers then independently extract the same metadata, bump `pyproject` on `staging`,
   dispatch `version-bump`, and close the issue (verified `major-bump-approval.yml` L101 "Handle /approve — bump version
   and dispatch"). Because PM is the version-surface SSOT, a double `version-bump` there is exactly where it most
   matters. The fix is a safe single-file delete.

2. **`main` and `staging` backmerge use divergent concurrency groups — contract violation, not a clobber risk
   (severity corrected on re-verification).** `main-backmerge-to-ldr.yml` (group `main-backmerge-to-ldr`) and
   `staging-backmerge-to-ldr.yml` (group `backmerge-to-ldr`) use **different concurrency groups**, so GitHub does not
   serialize them — directly contradicting staging-backmerge's own header comment ("Concurrency: keyed on the
   destination ref so simultaneous back-merges serialize (shared with main-backmerge so the two never race the same LDR
   push)"). **However, both push to LDR `--ff-only` with a 5× retry-on-race loop and never force-push** (verified:
   main-backmerge L144–150, staging-backmerge L102–108), so a genuine concurrent push cannot corrupt or overwrite LDR —
   the loser of the race retries, and on retry-exhaustion opens a visible PR per the safety contract. So the real cost
   is **avoidable retry churn + a self-contradicting documented invariant**, not lost writes. The fix (align the groups
   to the documented `backmerge-to-ldr`) is trivial and worth doing, but this is a P2 maintainability/noise item, not a
   P1 correctness defect. Both templated (main ×25, staging ×17).

### C. No-op — emits into the void (decide: wire a consumer, or delete)

| Workflow                     | Evidence                                                                                                                                                                                                                   |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schema-changed-handler.yml` | It IS triggered (`schema-changed` emitted by all 25 `semver-agent.yml`), greps codex/cursor-rules, then dispatches `rules-alignment-check` — which has **0 consumers fleet-wide**. Its core action is a Slack-noise no-op. |

### D. Vestigial dispatch TYPE only — keep the workflow, prune the unused `types:` entry

> These are **NOT dead workflows** (the narrow audit risked reading them that way). They are alive via cron + a live
> dispatch; only one _unused_ `repository_dispatch` type should be pruned.

| Workflow                     | Alive via                                                                | Prune unused type                                    |
| ---------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------- |
| `ldr-to-main-promote.yml`    | `schedule: */15` + `workflow_dispatch`                                   | `repository_dispatch: [ldr-to-main]` — 0 emitters    |
| `ldr-to-staging-promote.yml` | `schedule: 17 */6` + `tier-ab-green` (emitted by `ci-status-update.yml`) | `repository_dispatch: [ldr-to-staging]` — 0 emitters |

### E. Dormant / staged — DO NOT delete (false-positive corrections vs the narrow audit)

| Workflow                     | Why it is NOT cruft                                                                                                                                                                                                                                             |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `publish-package.yml`        | Its emitter exists as a **propagation template** (`scripts/propagation/templates/publish-package.yml`) — staged but **not yet rolled out** to repos' `.github/workflows/`. Consumer is dormant _pending template rollout_, not dead.                            |
| `auto-merge-minor-fixes.yml` | `sit-validated`: **0 emitters fleet-wide** (the narrow audit hedged "emitter in consumer templates" — there is none, not even a template) AND `dry_run` defaults `true`. Genuinely unwired. Decide: wire `sit-validated` (from `sit-unlock` on pass) or delete. |

### F. tab-mirror — bigger than "a dead file" (correction)

CLAUDE.md states `tab-mirror-to-ldr.yml` is "DISABLED fleet-wide" under Path-B. **It is not disabled** — the file still
carries a live `schedule: */15` sweep job, running across **all 25 repos** (~2,400 invocations/day). And **13–21 stale
`tab/*` branches per repo remain on origin** (PM 21, execution-service 13, UAC 17) — the sweep evaluates them for
divergence/stranding and can emit "stranded/diverged tab" **alerts** about Path-B-orphaned branches. So it is
noise-generating, not silently inert.

### G. Band-aid consolidation candidates (refactor — lower priority, verified)

- **SIT lock-liveness has 3 overlapping mechanisms.** `sit-starvation-detector.yml`'s _sole_ remediation action is
  `gh workflow run sit-debounce-trigger.yml` (line 142) — a second cron (`*/15`) that only re-pokes the first cron
  (`*/5`, which already auto-clears stale locks in-code). Fold the detector into the debounce workflow.
- **Two fleet CI-health crons converge.** `ci-status-reconciler.yml` (`*/10`) and `ci-failure-watcher.yml` (`*/15`) both
  poll `quality-gates-v2` conclusions fleet-wide; differ only in remedy (reconcile manifest vs escalate stuck PRs).
  Merge into one `ci-health.yml` with two jobs.
- **Two band-aids for one suppressed trigger.** `main-backmerge`'s `*/20` drift-tick exists because `[skip ci]` main
  commits suppress its `push:main` trigger; `promotion-lag-monitor.yml` is a _second_ workflow that pages when that
  drift-tick fails. Consolidate the drift-sweep + lag-page into one branch-health monitor.
- **Duplicated in-GHA Claude-spawn scaffolding.** `rules-alignment-agent.yml`, `plan-health-agent.yml` (daily job), and
  `downstream-fix-agent.yml` each reimplement the same `claude --print` scaffold three ways. Extract one
  `agent-runner.yml` (`workflow_call`, `inputs: {prompt, model, files_glob}`). `conflict-resolution-agent.yml` is now a
  thin shim that only re-dispatches to `escalate-to-orchestrator` — collapse it in (escalate already accepts
  `repository_dispatch`).

---

## Why it matters

- **Correctness:** the duplicate `/approve` handlers (B1) are a real (if low-frequency) defect — a human `/approve` on
  a MAJOR-bump issue double-bumps the version + double-dispatches `version-bump` on PM, the version SSOT. (B2 is **not**
  a correctness defect after re-verification — FF-only + 5× retry + never-force means it cannot clobber LDR; it is a
  contract violation + retry churn, folded into Noise below.)
- **Noise & cost:** the B2 backmerge groups (contradicting their own documented "shared" invariant) cause avoidable
  retry churn; tab-mirror (F) runs ~2,400×/day fleet-wide as a no-op, auto-rebases/force-pushes orphaned `tab/*`
  branches, and POSTs an orchestrator webhook every run;
  `downstream-fix-agent` (A) burns paid API on a manual-only path; `schema-changed-handler` (C) Slack-pings on a no-op.
- **Maintainability:** every extra workflow is one more thing to keep green during a node24/action bump (the 2026-06-08
  / 2026-06-10 bumps each touched ~all of these mechanically). Fewer, consolidated workflows = less drift surface.

## Recommended decision

Sequence lowest-risk → highest-value. **All deletes are PM-only / in-place except where flagged "templated".**

### Tier 1 — delete confirmed-dead (PM-only, in-place)

- [ ] [SCRIPT] P1. Delete `downstream-fix-agent.yml` (`unified-trading-pm`) — `downstream-fix-needed` has 0 emitters
      fleet-wide; also remove/repoint the `test_cascade_flow.py` assertion in `system-integration-tests` that expects it
      wired. If breaking-dep auto-fix is still wanted, route via `escalate-to-orchestrator` (`wall_type=ldr_qg_failure`
      already exists).
- [ ] [SCRIPT] P1. Delete `contract-replay.yml` + `contract-drift-record.yml` (`unified-trading-pm`) — echo-only stubs,
      0 callers, superseded by `cassette-drift-check.yml`.
- [ ] [SCRIPT] P1. Delete `request-major-bump-reusable.yml` (`unified-trading-pm`) — 0 `uses:` callers; identical to
      `request-major-bump.yml`.

### Tier 2 — fix B1 (real defect) + align the backmerge concurrency contract

- [ ] [SCRIPT] P1. Resolve the duplicate `/approve` handler (`unified-trading-pm`, PM-only) — delete
      `major-bump-approval.yml` to restore the single fleet-standard `major-bump-issue-handler.yml`, OR (if its richer
      `notify`+`persist`+`major-bump-approved` label behaviour is wanted) port that into the templated handler and
      delete the templated one's redundancy. **Operator pick required** — flag which handler is canonical.
- [ ] [SCRIPT] P2. Align `main-backmerge-to-ldr.yml`'s concurrency group to the documented `backmerge-to-ldr` (the
      value staging-backmerge already uses and both headers claim is "shared") so the two serialize as designed. **Not a
      correctness fix** — both already push FF-only + 5× retry + never-force, so this only removes avoidable retry churn
      and makes the code match its own stated invariant. **Templated** — edit `scripts/workflow-templates/` SSOT +
      `rollout-workflow-templates.sh` + commit fleet-wide.

### Tier 3 — no-op + vestigial cleanup

- [ ] [SCRIPT] P2. `schema-changed-handler.yml` (`unified-trading-pm`) — either wire a `rules-alignment-check` consumer
      (if codex-alignment-on-schema-change is still wanted) or delete the workflow; today it emits into the void.
- [ ] [SCRIPT] P2. Prune the unused `repository_dispatch` type `ldr-to-main` from `ldr-to-main-promote.yml` and
      `ldr-to-staging` from `ldr-to-staging-promote.yml` (`unified-trading-pm`) — keep the workflows (cron +
      `tier-ab-green` are live).
- [ ] [SCRIPT] P2. Decide `auto-merge-minor-fixes.yml` (`unified-trading-pm`) — wire `sit-validated` emission from
      `sit-unlock` on SIT pass + flip `dry_run` default, or delete. Currently unreachable.

### Tier 4 — tab-mirror retirement (templated + branch cleanup)

- [ ] [SCRIPT] P2. Delete stale `tab/*` branches fleet-wide (13–21 per repo on origin) now that Path-B slots live on LDR
      — confirm none carry un-preserved WIP first (cross-check `origin/wip-preserve/slot-*`).
- [ ] [SCRIPT] P2. Retire `tab-mirror-to-ldr.yml` (or gate its cron behind `if: false`) via the template SSOT + rollout;
      **correct the CLAUDE.md "DISABLED fleet-wide" claim** which is currently false (the cron still runs).

### Tier 5 — band-aid consolidation (refactor)

- [ ] [SCRIPT] P3. Fold `sit-starvation-detector.yml` into `sit-debounce-trigger.yml` (its only action re-pokes that
      workflow).
- [ ] [SCRIPT] P3. Merge `ci-status-reconciler.yml` + `ci-failure-watcher.yml` into one `ci-health.yml` (two jobs, one
      cron).
- [ ] [SCRIPT] P3. Consolidate `main-backmerge` `*/20` drift-tick + `promotion-lag-monitor.yml` into one branch-health
      monitor.
- [ ] [SCRIPT] P3. Extract a shared `agent-runner.yml` (`workflow_call`) for `rules-alignment-agent` +
      `plan-health-agent`; collapse `conflict-resolution-agent.yml` into `escalate-to-orchestrator.yml`. Migrate the two
      paid-`ANTHROPIC_API_KEY` agents to the VM orchestrator per the documented Phase-2 plan.

## Codex SSOT updates (on execution)

- `codex/08-workflows/ci-cd-flow.md` — correct the tab-mirror "DISABLED fleet-wide" statement; document the canonical
  major-bump handler once B1 is resolved; reflect any merged backmerge/CI-health workflows.

## Verification appendix (commands, for re-audit)

- Emitters of `<ev>`: `grep -rln -E "event_type[\"'\\\: =]+[\"']?<ev>\b" */ ` across all 25 slot worktrees (validate
  against controls `version-bump`/`qg-passed`/`tier-ab-green` first).
- Callers of a reusable: `grep -rn "<file>.yml" */ | grep uses:`.
- Stale tab branches: `git -C <repo> ls-remote --heads origin 'tab/*' | wc -l`.
