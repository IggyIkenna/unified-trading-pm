---
doc_type: issue
title:
  "quickmerge.sh --agent's already-committed fast path skips the `Quickmerge:` trailer, self-blocking the documented
  worker ship flow"
summary: >
  The documented worker ship flow (RULES.md §2 / worker.md §5: commit your code, run `bash scripts/quality-gates.sh`
  (Pass 1, writes `.qg_last_passed_sha` = the committed HEAD), then `quickmerge.sh "<msg>" --agent --files <paths>`
  (Pass 2)) reliably self-blocks at the local `pre-push-strict-quickmerge.sh` hook. Root cause: when quickmerge's
  `--files` set has nothing staged at invocation time (because the worker already committed, per the docs), quickmerge
  takes the `_QM_ALREADY_COMMITTED=1` fast path (`scripts/quickmerge.sh` around line 1498) which skips straight to `git
  push` — but the `Quickmerge: <agent|human>` trailer is only stamped inside the `git commit` branches (the
  normal-commit path and its pre-commit-retry path), never on the already-committed fast path. The resulting push then
  fails the local `pre-push-strict-quickmerge.sh` hook (`check_strict_quickmerge.py --block`), which requires every code
  commit reaching `live-defi-rollout` to carry the trailer unless it matches a carve-out.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, quality-gates, strict-quickmerge, pre-push-hook, tooling-gap, agent-mode]
related:
  [
    features_service_raw_ldr_pushes_bypass_quickmerge_2026_07_13.md,
    quickmerge_untracked_new_files_silent_noop_2026_06_23.md,
    qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md,
  ]
created: "2026-07-14"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: unified-trading-pm@431fda545 (fix, slot 4) + this sweep (slot 14, 2026-07-14)
source:
  [
    scripts/quickmerge.sh:1471-1501,
    scripts/dev/hooks/pre-push-strict-quickmerge.sh,
    scripts/cicd/check_strict_quickmerge.py,
  ]
---

# quickmerge.sh --agent's already-committed fast path skips the `Quickmerge:` trailer

## What I found

Shipping a single-file `unified-api-contracts` data fix
(`qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md` todo — the UCL Polymarket mapping), I followed the
documented worker flow exactly:

1. `git add <files> && git commit -m "feat(...): ..."` — HEAD = `23be88ff`.
2. `bash scripts/quality-gates.sh` — full run PASSED, wrote `.qg_last_passed_sha=23be88ff...`.
3. `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` — Stage 3 verified the SHA sentinel
   (`✅ SHA sentinel verified`), Stage 4/5 proceeded, and since nothing was staged (my files were already committed in
   step 1) it took the `_QM_ALREADY_COMMITTED=1` fast path (`scripts/quickmerge.sh` ~line 1498:
   `"Working tree clean ... changes already committed. Proceeding to push."`) straight to
   `git push -u origin "$BRANCH"`.
4. The local `pre-push-strict-quickmerge.sh` hook ran `check_strict_quickmerge.py --block` over the pushed range and
   failed:
   `❌ strict-quickmerge: 1 code commit(s) bypassed quickmerge: - 23be88ff ... [source changed without quickmerge: [...sports_mappings.py]]`.
   The push was rejected.

Reading `scripts/quickmerge.sh` around the commit stage (~1465-1501): the `Quickmerge: <kind>` trailer
(`_QM_COMMIT_MSG`) is only ever attached inside the actual `git commit -m "$_QM_COMMIT_MSG"` calls — the normal path and
its pre-commit-retry path. The `_QM_ALREADY_COMMITTED=1` branch never touches the commit message; it just pushes
whatever is already on HEAD. Since the mandated `--agent` flow requires the worker to commit BEFORE Pass-1 QG (the
sentinel is `git rev-parse HEAD`, which must already exist and be a real commit for `--agent` Stage 3 to accept it —
confirmed there is no dirty-tree / staged-only sentinel path), every single-repo `--agent` ship that doesn't happen to
have leftover staged diffs at Stage 5 hits this exact fast path and produces a trailer-less commit.

## Why it matters

This is a straightforward reproduction of the documented, mandated flow (RULES.md §2, worker.md §5 step a/a2) hitting a
hard local block via the very hook installed to enforce quickmerge usage (`pre-push-strict-quickmerge.sh`, "operator
policy 2026-06-26: every code push goes via quickmerge — no direct-push bypass"). The irony: the worker DID ship via
quickmerge (both passes, sentinel-verified), but the trailer that proves that lineage was never stamped because of this
fast-path gap. Any worker following the docs literally for a single-repo, single-commit `--agent` ship is likely to hit
this — it is not specific to this task or repo. The only sanctioned recovery listed in the hook's own header comment is
`git push --no-verify`, which CLAUDE.md's HARD RULE explicitly forbids agents from using without explicit user request
("NEVER skip hooks... unless the user has explicitly asked for it").

## Workaround used this session (not a fix — documented for traceability)

Rather than patch the shared `scripts/quickmerge.sh` (high blast-radius, concurrently used by the whole fleet)
unilaterally mid-task, or use `--no-verify` (banned), I worked around it for my own ship by:

1. `git reset --soft HEAD~1` (un-commit my change, keep it staged — no data lost, matches the doc's own recovery pattern
   for "ahead" repos).
2. Re-ran `bash scripts/quickmerge.sh "<msg>" --files '<paths>'` WITHOUT `--agent` — non-agent mode re-runs the FULL
   internal quality-gates.sh itself (Phase 1 lint-fix, Phase 2 lint-verify, Phase 3 full gates minus lint) and, since
   files were staged (not pre-committed), took the NORMAL commit path, which correctly stamps `Quickmerge: human`. Push
   succeeded; `check_strict_quickmerge.py` confirmed `✅ ... no bypassed code commits`.

This is slower (re-runs the full gate a second time) but stays within sanctioned tooling — no hook skipped, no shared
script touched under task pressure. Landed as `unified-api-contracts@aaa07df4`.

## Recommended decision

Fix `scripts/quickmerge.sh`'s `_QM_ALREADY_COMMITTED=1` branch (around line 1498, right before the `git push`) to check
whether `git log -1 --format=%B` already contains a `Quickmerge:` line, and if not, `git commit --amend` to append the
`Quickmerge: <human|agent>` trailer before pushing — mirroring what the normal commit path already does, just applied
retroactively to the pre-existing commit. This is a small, mechanical, carve-out-sanctioned change (`scripts/**` in
`unified-trading-pm` — CLAUDE.md's closed carve-out #3 for direct pushes "that must reach main to unblock the
pipeline"), but given it touches the fleet's shared ship mechanism used concurrently by every slot, it should land as
its own reviewed change rather than be folded into an unrelated task's diff.

## Todos

- [x] ✅ [INFRA] P2. In `scripts/quickmerge.sh`'s `_QM_ALREADY_COMMITTED=1` branch (~line 1498), amend the existing HEAD
      commit to add the `Quickmerge: <human|agent>` trailer (via `_QM_TRAILER_KIND`, already computed above that branch)
      if the commit message doesn't already carry one, before the `git push`. Verify against a real `--agent`
      single-repo ship (commit → quality-gates.sh Pass 1 → quickmerge --agent) that the resulting push no longer trips
      `check_strict_quickmerge.py`/`pre-push-strict-quickmerge.sh`. (repo: unified-trading-pm) —
      unified-trading-pm@431fda545
- [x] ✅ [INFRA] P3. Sweep recent `live-defi-rollout` history across repos for other trailer-less
      already-committed-fast-path pushes that may have landed via `--no-verify` or a hook-less clone (this doc's audit
      only checked `unified-api-contracts`'s last ~20 commits) — confirm whether this is a widespread,
      silently-tolerated gap or mostly caught by the hook as it was here. (repo: unified-trading-pm) — see Progress Log
      2026-07-14 slot 14 entry: 168 genuine trailer-less bypass commits found across 15/24 repos in the last 30 days —
      widespread, not a one-off. Todo 1's fix (landed same day, `431fda545`) should close it going forward.

## Progress Log

**2026-07-14, slot 13 (data_engineering)**: discovered while shipping the UCL Polymarket-mapping fix
(`qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md`). Reproduced with the exact documented worker flow;
traced root cause in `scripts/quickmerge.sh`; worked around via non-agent quickmerge (full internal QG re-run + own
commit) rather than patching the shared script or using `--no-verify`. Filed this doc per findings-closure discipline;
did not implement the fix (out of data-craft scope, and too high-blast-radius for an inline hotfix on a shared,
concurrently-used script).

**2026-07-14, slot 4 (infra)**: implemented the recommended fix exactly as specced. In the `_QM_ALREADY_COMMITTED=1`
branch, check `git log -1 --format=%B | grep -q '^Quickmerge:'`; if absent, write the existing HEAD message + a fresh
`Quickmerge: ${_QM_TRAILER_KIND}` trailer to a temp file (`mktemp "${TMPDIR:-/tmp}/qm-amend-msg.XXXXXX"`, matching the
script's existing tempfile convention) and `git commit --amend -F <file>` before the push. Verified in two stages: (1)
scratch-repo repro — built a disposable bare-origin + clone, committed a source-file change with no trailer, confirmed
`check_strict_quickmerge.py --block` flags it (`❌ ... bypassed quickmerge`), applied the fix's exact amend logic,
re-ran the checker — passed clean; also confirmed idempotency (no re-amend / SHA unchanged when a trailer is already
present). (2) Live production verification — shipped this very fix through PM's own `--agent` two-pass flow; PM is
extremely high-churn (commits landing every 5-260s from concurrent slots), so quickmerge's Stage 0.4 rebase kept
invalidating the Pass-1 sentinel (a rebase mints a new SHA even for a content-identical replay, so the content-scoped
sentinel fallback — which requires ancestor-not-rebase — never applies here); looped rebase→QG→`quickmerge --agent` and
succeeded on the 3rd attempt. The live log confirmed the exact new code path firing:
`"changes already committed but missing the Quickmerge trailer; amended HEAD to add 'Quickmerge: agent'. Proceeding to push."`
followed by `✅ strict-quickmerge: no bypassed code commits` — the hook that used to reject this exact scenario now
passes. Landed as `unified-trading-pm@431fda545` (PR #1014, auto-merge). Todo 1 done; todo 2 (sweep for other
trailer-less already-committed pushes) left for a follow-up task — out of scope for this fix.

Side-finding (not fixed here, noted for awareness): running quickmerge WITHOUT `--agent` on `unified-trading-pm` itself
triggers Phase-1's tree-wide lint-fix (ruff+Prettier over the whole repo, ~1900 files), which in turn breaks
`workspace-manifest.json`'s canonical-format gate (`STAGE 6` `manifest-canonical` check) — the non-agent fallback the
prior session used successfully on `unified-api-contracts` does NOT work on PM itself. Discarded the resulting unstaged
tree-wide diff via `git restore .` (verified it was pure auto-fix churn from this session, not foreign WIP) and shipped
via `--agent` instead.

**2026-07-14, slot 14 (infra)**: closed todo 2 (the sweep). Wrote a standalone Python script (scratchpad, not committed
— see below) that ports `check_strict_quickmerge.py`'s exact `commit_violates()`/`_on_promoted_tip()` logic (same
merge/promoted-tip/bot/skip-ci/carve-out exemptions) and runs it per-repo over
`git rev-list --since '30 days ago' origin/live-defi-rollout` across all 24 repos under this slot's worktree. First pass
over-counted: 319 "violations", because the sweep only fetched `origin/live-defi-rollout` and never
`origin/main`/`origin/staging`, so `_on_promoted_tip()`'s ancestor check silently failed for every already-promoted
backmerge commit (123 of the 319 were `chore(promote): LDR → main (Option-B direct)` commits, verified false-positive
via `git merge-base --is-ancestor` after fetching `origin/main` fresh — exactly the fail-safe over-flagging the check's
own docstring warns about). Re-ran with `origin/main` + `origin/staging` fetched fresh per repo before the walk:

**168 genuine trailer-less bypass commits** remain (0 of them `chore(promote)` — all real conventional-commit
fix/feat/refactor messages), spanning **15 of 24 repos** in the last 30 days: unified-api-contracts 35,
unified-trading-library 29, deployment-api 25, market-tick-data-service 22, deployment-service 17, deployment-ui 16,
instruments-service 13, execution-service 4, strategy-service 3, agent-orchestrator 2, alerting-service 1, ml-service 1.
Clean (30d): batch-live-reconciliation-service, client-reporting-api, e2e-testing, features-service,
fund-administration-service, greeks-service, ibkr-gateway-infra, market-data-processing-service,
system-integration-tests, trading-agent-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui.

All 168 postdate the hook's 2026-06-26 install (61 landed 2026-07-13/14, i.e. in the ~36h before this fix shipped), and
authorship spans both slot-VM (`slot-N·planning`) and operator-laptop (`main·laptop`/`main·harsh_pc`) origins — **this
confirms a widespread, silently-tolerated gap, not a one-off the hook mostly caught.** Every sample checked matches this
doc's diagnosis exactly (real message, no `Quickmerge:` trailer, not a promote/backmerge, not bot/skip-ci) — consistent
with every one of them hitting the `_QM_ALREADY_COMMITTED=1` fast-path gap that todo 1's fix (already landed same day,
`unified-trading-pm@431fda545`) closes going forward. Did not investigate further why the pre-push hook itself let these
168 through locally (hook-not-installed-yet on that clone vs. `--no-verify` vs. stale hook copy) — that's a distinct
question from "is the gap widespread" and out of scope for this P3 todo; flagging as a possible follow-up if the pattern
recurs post-fix. Sweep script kept at this session's scratchpad only (not committed — throwaway analysis tool, not
project code).
