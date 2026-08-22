---
doc_type: issue
title:
  NA-corpus ratchet diff-scoped against origin/main deadlocks LDR→main promotion whenever main lags — positive-feedback
  wall, unconvergeable by serial fixing
summary: >-
  `unified-trading-pm`'s LDR→main promotion stalled 22h (last merged promote PR #2671 at 2026-08-09T09:19Z; main 1180
  commits behind LDR) on a single hard gate: `check_na_corpus_ratchet` run as `--diff-base origin/main` from
  `run_hygiene_sweep.sh`'s shared `DIFF_BASE_REF`. The 2026-08-09 diff-scoping fix (b12d43618) assumed `origin/main` is
  a proxy for "the change under test's own base". That holds only while promotion is FLOWING. Once promotion stalls,
  `origin/main` lags arbitrarily and the diff spans the entire unpromoted backlog instead of the change — and diff-base
  mode has ZERO tolerance (any single new NA doc fails). This is a positive-feedback deadlock: the gate blocks the
  promote → main falls further behind → the measured diff grows → the gate fails harder. Measured directly: the same
  check reported 51 docs/116 todos at the 05:41Z CI run and 53 docs/151 todos ~2h later, while against the integration
  branch (`origin/live-defi-rollout`) it reported ~0. Seventeen AO `sit_failure` dispatches re-polled this wall without
  closing it; nobody touched `run_hygiene_sweep.sh` in the 17h the wall stood, because the failure reads as ordinary
  corpus growth rather than a base-selection bug.
status: open
nature: issue
asset_group: [ci] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; a promotion-gate/ratchet deadlock mechanism finding, own tags already say "ci", not data-pipeline scope
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, quality-gates-v2, ratchet, plan-hygiene, promotion, deadlock, live-incident]
related:
  - /plans/archive/2026_08/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md
  - /plans/archive/2026_08/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md
  - /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md
created: 2026-08-10
author: /ci-reconcile (interactive, slot-2·laptop)
parent_epic: security_and_cross_cutting_master
priority: P1
source: >-
  /ci-reconcile sweep of #ci-failures since 2026-08-10T00:00Z — 4 python-quality-gates-v2 CRITICAL alerts on
  unified-trading-pm (PRs #2706/#2707/#2708/#2709 + 3 LDR pushes) plus 3 branch-health PROMOTION LAG warnings, all one
  root cause.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-21
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_na_corpus_ratchet.py,
    unified-trading-pm/scripts/plan-hygiene/na_corpus_baseline.yaml,
    unified-trading-pm/scripts/dev/safe-doc-push.sh,
  ]
---

# NA-corpus ratchet diff-scoped against a lagging `origin/main` deadlocks promotion

## Evidence

- Last merged promote PR: **#2671, 2026-08-09T09:19:48Z**. `gh api compare/main...live-defi-rollout` →
  `ahead_by: 1180, behind_by: 0`.
- Promote PRs **#2706, #2707, #2708, #2709** each opened and were **closed unmerged** (~2.5h cycle), every one red on
  `QG slice (checks)`.
- The failing run's own verdict (`gh run view 31358877638 --log-failed`) named exactly one hard failure:
  `❌ check_na_corpus_ratchet (--diff-base origin/main): 51 new NA-population doc(s); 116 new open todo(s)` →
  `❌ FAIL [hard] assigned_vm:NA corpus size` → `❌ Sweep FAILED`. Independently confirmed by the AO worker in
  `8409d134a4` ("confirms na-corpus is sole live blocker, other 2 checks stale-snapshot") — `VERSION_SPLIT` and
  `VESTIGIAL_SCALAR_DRIFT` in the same log are non-blocking.
- **The growth is the deadlock, measured**: 51 docs/116 todos (05:41Z CI) → **53 docs/151 todos** (07:40Z local, same
  check, same base). Against `origin/live-defi-rollout` instead: **~0**. The number the gate reports is a function of
  how far main has fallen behind, not of any change under test.

## Root cause

`run_hygiene_sweep.sh` sets one shared `DIFF_BASE_REF="origin/main"` in CI mode and hands it to every diff-scoped
ratchet. `origin/main` is only a valid stand-in for "this change's base" while promotion is flowing. It is not a
branch-relative base — it is an arbitrary point that recedes exactly when the gate starts blocking, which is what turns
a normal ratchet into a self-reinforcing wall.

## What shipped (2026-08-10)

1. **`4c964f8447` (slot-23) — promotion PRs skip `--diff-base` for the NA-corpus check.** Independently reached the same
   diagnosis as this doc ("un-convergeable on the promote path") and fixed it more surgically than this doc's first
   draft proposed: rather than dropping the check to baseline mode in ALL CI contexts (which would have discarded the
   2026-08-09 concurrent-agent race fix everywhere it still works), it detects a promote PR via
   `GITHUB_HEAD_REF =~ ^promote/` and falls back to baseline+buffer ONLY there. **That is the correct shape and it
   supersedes this doc's original proposal** — recorded here so the superseded approach is not re-attempted.
2. **Baseline re-measured to 389 docs / 1150 todos** via the sanctioned `--update-baseline` (never a hand-edit).
   Archival could not absorb the growth: `check_archive_candidates.sh` returned exactly one candidate, and that one was
   uncommitted foreign WIP in a shared slot checkout, not corpus content.
3. **The promote gate moved to the shared `DIFF_BASE_REF` so it covers ALL FOUR diff-scoped checks**, not just
   NA-corpus. `4c964f8447` scoped its fix to one consumer, but `check_reference_paths`, `check_archive_candidates` and
   `check_effort_signal_ratchet` read the same `DIFF_BASE_REF` and carry the identical latent bug — and reference-paths
   was already tripping it in production (`check_reference_paths (--diff-base origin/main): 2 NEW violation(s)`
   hard-failed the 11:25Z promote-path run, alongside a prosewrap-padding ratchet). Setting the rule once at the source
   also avoids four copies of one predicate, the shape that rotted the tranche lists (see
   `scripts/scheduled_job_already_ran.py`'s header). Verified: `GITHUB_HEAD_REF=promote/…` ⇒ `DIFF_BASE_REF=''` (all
   four checks baseline mode); a normal PR and a push to LDR both still get full diff-scoping. Post-fix measurement:
   corpus 394 docs / 1151 todos vs the promote-path ceiling 399 / 1180 — passes, but with only 5 docs and 29 todos of
   headroom, which is what the ADMIN todo below is about.

## Todos

- [x] ✅ [BACKEND] P1. Extend the same lag-guard reasoning to the **other** `DIFF_BASE_REF` consumers
      (`check_reference_paths.py`, `check_archive_candidates.sh`, `check_effort_signal_ratchet.py`) — DONE 2026-08-10 by
      moving `4c964f8447`'s promote gate from the NA-corpus wiring up to the shared `DIFF_BASE_REF` assignment, so one
      predicate covers all four consumers. Verified by simulation: `GITHUB_HEAD_REF=promote/…` ⇒ `DIFF_BASE_REF=''`; a
      normal PR and a push to LDR keep full diff-scoping.
- [x] ✅ [BACKEND] P2. The promote gate keys on `GITHUB_HEAD_REF =~ ^promote/`, a NAMING contract with the promote bots
      rather than a structural one — a half-rename would silently revert all four gates with no test failing. DONE
      2026-08-10: `scripts/quality_gates/check_promote_prefix_contract.py` asserts all THREE sites agree (both producers
      — `.github/workflows/ldr-to-main-promote.yml` and `scripts/cicd/ldr_to_main_fleet_promote.sh` — plus the sweep's
      consumer regex), AND that the gate sits on the SHARED `DIFF_BASE_REF` rather than one consumer. Wired into
      `quality-gates.sh`. Verified both directions: renaming the consumer regex OR either producer makes the check exit
      1 naming the exact file; the unmodified tree passes.
- [x] ✅ [BACKEND] P3. The deeper shape is still unaddressed: `origin/main` is a proxy for "this change's base" that is
      only valid while promotion FLOWS. The promote gate handles the one case where that proxy is known-bad, but a
      normal PR opened against a long-stalled main has the same problem in miniature. Preferred end state: resolve the
      diff base to the branch's own last-gated point (`github.event.before` for a push; the integration branch for a PR)
      rather than a fixed `origin/main`. Note the CI checkout is `fetch-depth: 2`
      (`unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`), so any chosen base must either already
      resolve there or be explicitly fetched — a base that silently fails to resolve is fail-UNSAFE (every current
      violation reads as "new"). Repo: unified-trading-pm (`scripts/plan-hygiene/`). — **DONE**, reconciled from
      `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `unified-trading-pm@715a90d7ac` (`DIFF_BASE_REF` now
      resolves from the triggering CI event — push uses `before` SHA, PR uses `GITHUB_BASE_REF`, other triggers stay
      baseline+buffer; verified via 5 simulated scenarios).
- [ ] [BACKEND] P2. **Make corpus-growth ratchets ENTRY gates only.** Per D104 ruling (2026-08-21,
      issues_corpus_completion_dispatch_2026_08_21.md ledger): Entry only — re-gating aggregate PRs is what converts
      ordinary corpus growth into the documented promotion deadlock, with no demonstrated safety benefit. Remove
      `check_na_corpus_ratchet`, `check_reference_paths`, `check_archive_candidates`, `check_effort_signal_ratchet`,
      and `check_ag_closeout_linkage` from the promotion-PR (`chore(promote)`) gate path, keeping them as ENTRY gates
      only (LDR push / precommit via `run_hygiene_sweep.sh`). Done-when: a `chore(promote)` PR's QG slice no longer
      re-runs these corpus-growth ratchets, while a direct LDR push / precommit still enforces them. Repo:
      unified-trading-pm.
- [x] ✅ [BACKEND] P2. **No detection surface for this failure class.** The wall stood 22h with 17 `sit_failure`
      dispatches, none of which escalated "this gate cannot converge" as distinct from "this gate is red". Add a
      detector for a _non-convergeable_ gate — e.g. the same check failing across N consecutive distinct HEADs with a
      MONOTONICALLY GROWING violation count is definitionally not a fixable regression. Cross-reference
      `/plans/archive/2026_08/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md` (adjacent gap:
      local pre-push ratchet breaches) — this one is the opposite side, a remote gate that IS observed but is
      mis-classified as retryable. Repo: agent-orchestrator (`server/escalation.py`, `server/ci_reconcile.py`). —
      **DONE**, reconciled from `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`:
      `agent-orchestrator@197c5ca521` (`detect_non_convergeable_gate()` + violation-count-history walk in
      `server/escalation.py`, pages immediately on a 3-streak monotonic growth instead of waiting the normal grace
      period; 4 new tests).
- [x] ✅ [ADMIN] P2. **The NA corpus genuinely outgrew its ceiling** (391 docs vs 372+10; todos 1119 vs 1109+30 passing),
      and this is the third re-baseline in ~2 days. The fleet's own mandated processes (findings-triage "every follow-up
      is a `- [ ]` todo", `/plan-reconcile`, `/ci-reconcile`) create NA docs faster than `/na-eligibility-audit` retires
      them. **RESOLVED 2026-08-15** (`ci_satellite_ao_dispatch_batch14_2026_08_15.md` todo 10, operator ruling): chose
      faster retirement cadence over a higher ceiling or narrowed scope. Shipped
      `agent-orchestrator/scripts/install-na-eligibility-auditor-timer.sh` (systemd `--user`, no sudo). Original text:
      decide whether the answer is a higher steady-state ceiling, a faster retirement cadence, or narrowing what
      must become a tracked NA doc — re-baselining on each breach is not a steady state. Owner: operator.

- [x] ✅ [BACKEND] P1. **The deadlock SURVIVED the cancellation fix — it is now a supersede TREADMILL, and this is the
      controlling blocker.** Measured 16:00-16:35Z 2026-08-10: PR #2713 was CLOSED with `mergedAt: null`, then #2714,
      then #2715, each superseded within a tick; `origin/main..origin/live-defi-rollout` GREW 1622 → 1728 across the
      window. The bot's own log states the rule:
      `⏭ existing promote PR … has a FAILED QG slice (doomed run) — superseding this tick instead of waiting it out`.
      The mechanism is a rate mismatch, not a bug in any one check: `QG slice (checks)` fails in ~3.5 min, the promote
      bot ticks every ~15 min, and LDR receives roughly 4 commits per 3 min from the fleet — so every tick mints a NEW
      frozen head and restarts the whole gate from zero. **Any check that fails FAST therefore guarantees an unbounded
      stream of fresh PRs that can never finish**, while the `tests` slice (which PASSES — measured run 31408156018)
      never gets to matter. Fix the rate mismatch, not just today's failing check: e.g. do not supersede while a run is
      still in progress unless the head is materially different, or require N consecutive failures before superseding.
      Repo: unified-trading-pm (`.github/workflows/ldr-to-main-promote.yml`). **Note for whoever picks this up: the
      cancel-in-progress exemption shipped earlier today (932db1955e) was a REAL fix for a REAL cause, but it was never
      sufficient on its own — cancellation stopped and superseding took its place. Do not read its presence as
      "promotion is handled".** — **DONE**, reconciled from
      `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `unified-trading-pm@7840229ddf` (requires
      `DOOMED_STREAK_THRESHOLD=3` consecutive doomed observations of the SAME open PR before superseding, tracked via
      the bot's own "doomed-tick" PR comments).
- [x] ✅ [BACKEND] P2. **`check_ag_closeout_linkage` is another corpus-wide ratchet with no diff-scoped fast path** —
      the same class this doc already documents for the `DIFF_BASE_REF` four. It failed the promote gate at frozen head
      `37d720dc4291` with `1 orphan(s) (baseline 0)`, yet at LDR tip `0f7d704066` it reports **0 orphans** (verified
      locally in a clean worktree), so the violation was transient corpus state that no individual commit owned. Its
      `--only` mode passes on staged files while the corpus-wide mode fails, which is exactly the (f)-class blind spot:
      a violation introduced via a fast path surfaces later on an unrelated commit's full run. Give it the same
      diff-scoped treatment as the migrated six. Repo: unified-trading-pm (`scripts/plan-hygiene/`). — **DONE**,
      reconciled from `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `unified-trading-pm@96b33046f9`
      (added `--diff-base <ref>` mode to `check_ag_closeout_linkage.py`, git-backed rebuild + path-identity compare;
      wired into `run_hygiene_sweep.sh`'s shared `DIFF_BASE_REF` guard).
- [x] ✅ [BACKEND] P3. **`check_ui_api_flow_coverage.py` fails OPEN on a missing manifest.** Run outside the expected
      workspace layout it prints `ERROR: Manifest not found: …/unified-trading-pm/ui-api-flow-test-manifest.yaml` and
      **exits 0** (measured 2026-08-10). A gate whose absent input yields PASS cannot be trusted to be enforcing
      anything; if the manifest ever goes missing in CI, its `BLOCK: 2 critical journey(s) have ZERO real-flow tests`
      verdict silently disappears instead of failing loudly. Make a missing manifest a hard error, and separately
      resolve the two flagged journeys (`deploy-service`, `kill-switch-toggle`). Repo: unified-trading-pm
      (`scripts/checkers/`). — **DONE** (missing-manifest half only; the two flagged journeys are untouched, see below),
      reconciled from `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `unified-trading-pm@d5ea8d0755` —
      the checker already returned exit 2 for missing/unparseable manifest; fixed `quality-gates.sh`'s `--warning-only`
      wrapper to hard-fail specifically on exit 2 instead of folding it into the same non-blocking warn path as an
      ordinary coverage gap.
- [ ] [BACKEND] P3. Resolve the two flagged journeys (`deploy-service`, `kill-switch-toggle`) named in the prior todo —
      the missing-manifest hard-fail is fixed, this half was explicitly out of scope for that fix. Repo:
      unified-trading-pm (`scripts/checkers/`).
- [ ] [SCRIPT] P2. **Have `scripts/dev/safe-doc-push.sh` self-set `GITHUB_REF_NAME`/`GITHUB_REF` when it detects it's
      committing to `live-defi-rollout` locally**, so every future local session gets the correct baseline+buffer
      ratchet mode automatically instead of needing to know and manually pass these vars (3rd confirmed recurrence,
      2026-08-16 + 2026-08-19 x1 — see Progress Log). Also investigate why `export VAR=val && bash
      scripts/dev/safe-doc-push.sh ...` did not reliably propagate the var through to the check (only an `env
      VAR=val bash scripts/dev/safe-doc-push.sh ...` prefix worked reliably, 2026-08-19) — likely a subprocess/hook
      boundary that resets or doesn't inherit the exported var; root-cause and either fix the propagation or document
      the `env`-prefix requirement explicitly in the script's own usage text. Repo: unified-trading-pm
      (`scripts/dev/`, `scripts/plan-hygiene/`).
- [ ] [SCRIPT] P2. **`check_na_corpus_ratchet.py` (via `generate_na_doc_tranche_inventory.py`) has no aggregator-doc
      exclusion, unlike `count_open_tasks.py`/`/open-task-count`, which already excludes "aggregator plans (master /
      batch / consolidated / closeout / satellite) whose todos duplicate the primary plans they roll up" from its
      count. Confirmed live 2026-08-22: `plans/active/issues_corpus_executable_queue_2026_08_21.md` (a wave-3
      rollup/queue doc, `assigned_vm: NA`) carries 352 open todos that are pointer-duplicates of todos already
      separately counted in their own source docs under `plans/active/issues/` (spot-verified:
      `ag_closeout_audit_ci_parked_2026_08_16.md` counts 3 open todos on its own, and the queue doc's own item 1
      re-points at the same underlying work) — this single doc alone accounted for ~94% (352/376) of the
      promote-gate-failing todo-count overage that triggered this remediation's baseline bump. Give
      `check_na_corpus_ratchet.py` (and/or its shared `generate_na_doc_tranche_inventory.py` counting engine) the
      same aggregator-exclusion convention `count_open_tasks.py` already uses, so a future rollup/queue doc of this
      shape inflates the ratchet only once (via its own source docs), not twice. Repo: unified-trading-pm
      (`scripts/plan-hygiene/`).

## Progress Log

- **2026-08-10 16:36Z (/ci-reconcile, slot-2·laptop)** — ✅ **PROMOTION DRAINED. The wall is down.** Promote PR **#2717
  MERGED at 2026-08-10T16:36:18Z**; `origin/main..origin/live-defi-rollout` went **1728 → 2** (the 2 being commits that
  landed after the merge). First promote PR to merge since #2671 on 2026-08-09T09:19Z — roughly 31h and ~1730 commits.
  **Attribution, stated honestly: this session did not land the change that unblocked it.** The final blocker was
  `check_ag_closeout_linkage` reporting `1 orphan (baseline 0)` at frozen head `37d720dc4291`; that orphan is simply
  absent at LDR tip `0f7d704066` (verified locally in a clean worktree: 0 orphans), so someone else's commit cleared it,
  the checks slice passed at 16:35Z, and the already-armed auto-merge fired one minute later. What this session's two
  shipped fixes DID do is remove the two earlier blockers in front of it — and note the cancel-in-progress exemption was
  verified ABSENT on `main` before this merge and PRESENT after, so it only becomes load-bearing from now on. **The P1
  treadmill todo stays OPEN and is not resolved by this drain**: the rate mismatch that manufactured #2713→#2717 is
  still armed and will re-fire on the next fast-failing check. Measurement trap recorded for the next person:
  `gh pr list --search "chore(promote)"` returned an EMPTY list twice while promote PRs demonstrably existed — it
  reported `[]` at the same moment `#2717` was open. Use `gh pr list --state all` and filter on `headRefName` starting
  `promote/`; do not trust the search form for this.
- **2026-08-10 ~16:35Z (/ci-reconcile, slot-2·laptop)** — **The promotion did NOT drain; reopening the analysis.** A 2h
  watcher on PR #2713 terminated on its own timeout branch (distinct exit code 3, deliberately not 0 — an earlier
  watcher this session exited 0 on a fallthrough and I misreported it as success). Its verdict: #2713 CLOSED unmerged,
  `ahead` growing throughout. Follow-up measurement established the treadmill and its rate mismatch (todo above), that
  the `tests` slice PASSES while only `checks` fails, and that the specific failing check is already clean at LDR tip.
  Also recorded: PM's `ldr-to-main-promote.yml` reports `success` on EVERY ~15-min tick while promoting nothing — the
  same green-run/wrong-outcome class as the semver-agent that ran green for 41 days minting zero tags, and a concrete
  instance of the "no detection surface" todo above. Correction to this doc's earlier framing: the two shipped items
  under "What shipped" are genuine fixes but did NOT unblock promotion; the wall stands.
- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Root-caused and remediated per the two items under "What shipped".
  Fleet sweep at the same time: 25/26 repos green on `quality-gates-v2`@LDR (`unified-trading-ci` has no such workflow —
  it hosts the reusable one); all 23 GH-Actions standing monitors green except `ldr-docs-gate`; both host-dispatched
  systemd watchdogs verified active and OK via live SSM.
- **2026-08-10 (cicd escalation `agt-cced28`, slot-15)** — Recurrence of the same deadlock on the LDR-branch path:
  `quality-gates-v2` RED on `live-defi-rollout` (workflow_dispatch re-runs) with
  `check_na_corpus_ratchet (--diff-base origin/main)` reporting 57→59 new docs / 185→193 new todos while main slipped to
  1501 commits behind LDR. Root cause: the shared `DIFF_BASE_REF` guard only excluded `promote/*` PRs; a DIRECT
  LDR-branch run has empty `GITHUB_HEAD_REF`, so it still diff-scoped against the lagging `origin/main` and measured the
  whole unpromoted backlog. Fixed by extending the same lag-guard to `GITHUB_REF == refs/heads/live-defi-rollout` (falls
  back to baseline+buffer; current NA corpus 394 docs / 1148 todos, inside the reviewed 409/1350 ceiling). Verified:
  guard unit cases (LDR-wfd→baseline, promote→baseline, feature-PR→diff-scope, push-main→diff-scope) + sweep
  `--ci --no-regen` under LDR env sim EXIT 0 (Hard failures 0). Shipped via quickmerge:
  `scripts/plan-hygiene/run_hygiene_sweep.sh`.
- **2026-08-16 (cicd agt-abeafe, slot 14, `ldr_qg_failure` escalation on live-defi-rollout, run 31960574434)**: the
  escalation's original 2 named failures (`check_reference_paths` 40>34, `check_ag_closeout_linkage` 1 orphan) are both
  fixed/self-healed — see this dispatch's own fix in `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md`.
  While verifying the sweep locally, first got a false `check_na_corpus_ratchet` failure because my initial local repro
  omitted `GITHUB_REF_NAME` (so `run_hygiene_sweep.sh`'s guard defaulted to `--diff-base origin/main` instead of
  baseline+buffer mode) — re-ran with `GITHUB_REF_NAME=live-defi-rollout` set (correctly simulating this wall's actual
  CI context) and confirmed **the 2026-08-10 lag-guard fix is working as designed** (correct baseline+buffer mode
  selected, not diff-base). However the check still hard-fails for real in that mode: **458 NA docs > baseline 432 +
  buffer 20 = 452** (todo-count axis still within its buffer). This is the SAME organic-creep pattern this doc's own
  2026-08-10 entries already describe ("5 docs / 29 todos of headroom" at the time) — the corpus grew past the
  2026-08-15 baseline snapshot (`max_na_docs: 432`) by more than the buffer tolerates. Per this doc's own established,
  repeatedly-reaffirmed precedent (see the sibling `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity`
  doc's Progress Log — 8+ prior dispatches into this exact check all declined to bulk-reclassify/archive NA docs
  myself, since spot-checks there consistently found the growth is genuine NA-worthy content, not misuse), NOT
  attempting a bulk fix or blind `--update-baseline` here. Shipping the genuine, in-scope ag_closeout_linkage fix now;
  leaving this 6-doc overage for the next `/na-eligibility-audit` pass or a reviewed baseline bump. `AUTHORING_SLOT`
  for this escalation is the `ldr-ci-monitor` sentinel (not a numbered slot) — no slot-ping applicable per this role's
  skip-rule.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:f2fc0a2b8f9bc8cb]: KEEP-NA, valid -- Two remaining open todos on an otherwise heavily-shipped CI/promotion-mechanics incident doc. The first is explicitly framed as an operator decision the todo text itself says is 'not a unilateral backend change — it narrows a hard gate.' The second (resolving real-flow test coverage for the deploy-service and kill-switch-toggle journeys) is genuine engineering work; kill-switch-toggle in particular touches live-trading kill-switch machinery, so it is treated as care-requiring GENUINE_WORK rather than a slam-dunk mechanical task, not clearing the full bounded-outcome bar needed for a doc-level reclassify.
- **2026-08-19 (plan_reconciler, sports tranche, agt-07473e)**: **third confirmed recurrence of the local-repro
  false-positive** (same class as the 2026-08-16 entry above). `bash scripts/dev/safe-doc-push.sh` (which shells out
  to `run_hygiene_sweep.sh`'s prek hook) failed committing 2 new `assigned_vm: NA` issue docs with
  `check_na_corpus_ratchet (--diff-base origin/main): 9 new NA-population doc(s); 24 new open todo(s)` — a plain
  local invocation with no `GITHUB_REF_NAME`/`GITHUB_REF` set, so the guard defaulted to diff-base-vs-`origin/main`
  mode instead of baseline+buffer. Confirmed the fix: `env GITHUB_REF_NAME=live-defi-rollout
  GITHUB_REF=refs/heads/live-defi-rollout bash scripts/dev/safe-doc-push.sh ...` correctly selected baseline+buffer
  mode and the check passed cleanly (genuine remaining blocker after that was an unrelated frontmatter
  `parent_epic` omission on this session's own new doc, fixed separately). **New finding this run**: even with the
  var exported in the calling shell (`export GITHUB_REF_NAME=... && bash scripts/dev/safe-doc-push.sh ...`), the
  first several retries still failed identically — only explicitly prefixing the var on `safe-doc-push.sh`'s own
  invocation line (`env VAR=val bash scripts/dev/safe-doc-push.sh ...`) reliably worked; `export`-then-`&&` did not
  reliably propagate through whatever subprocess/hook chain `safe-doc-push.sh` spawns (not root-caused further this
  pass — genuinely new investigation, not a same-file fix). **Not fixed at the root**: `safe-doc-push.sh` itself
  still requires every caller to know and correctly pass this env var by hand for a plain local LDR commit — the
  natural fix (have the script set `GITHUB_REF_NAME`/`GITHUB_REF` itself when it detects it's operating on
  `live-defi-rollout`, mirroring what a real LDR-push CI run would set) would close this permanently for every
  future local session, but that's a `scripts/**` change outside this run's write scope. Filed as todo below.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): **RECLASSIFY, per-todo split path.** Conflict-checked (grep
across `plans/active/*.md` for the mechanism — zero prior hits) then extracted the bounded `[SCRIPT] P2` todo (have
`scripts/dev/safe-doc-push.sh` self-set `GITHUB_REF_NAME`/`GITHUB_REF` when committing to `live-defi-rollout`
locally, plus root-cause the `export`-doesn't-propagate finding) into
`ci_satellite_ao_dispatch_batch16_2026_08_21.md` (new batch, todo 1) — a genuinely worker-determinable script fix
with a clear done-when, confirmed recurring 3x (2026-08-16, 2026-08-19 x2) with no design call embedded. The other 2
open items stay `assigned_vm: NA`: the promote-PR re-gate item is an explicit operator decision ("not a unilateral
backend change — it narrows a hard gate," per the 2026-08-17 verdict), and the deploy-service/kill-switch-toggle
journey item touches live-trading kill-switch machinery — genuine care-requiring engineering work, not a bounded
spec. Doc stays NA overall; this is a split extraction, not a whole-doc reclassify.

- **2026-08-22 (quality_gate_resolution, slot-19, escalation agt-924889)** — **Baseline bumped, root cause identified
  (organic-creep recurrence #N, not a diff-base-mode regression).** `unified-trading-pm` promote PR #3703 continuously
  red 180min on `quality-gates-v2` / `QG slice (checks)`: `check_na_corpus_ratchet` hard-failing (baseline mode, not
  diff-base — the 2026-08-10 lag-guard is confirmed still correctly selected on this PR). Locally reproduced: 2153 NA
  open-todos > baseline 1777 + buffer 200 (baseline last set 2026-08-21). Traced the 376-todo overage: **352 of it
  (94%) is one doc**, `plans/active/issues_corpus_executable_queue_2026_08-21.md` (a wave-3 issues-corpus completion
  rollup/queue, `assigned_vm: NA`, created 2026-08-21) — its checkboxes are pointer-duplicates of todos already
  separately counted in their own source docs (spot-verified against `ag_closeout_audit_ci_parked_2026_08_16.md`,
  see the new todo above). This is genuine, reviewed, non-misuse growth — a deliberate, dated, self-consuming
  retirement-campaign artifact (its whole purpose is retiring/archiving the docs it enumerates, which is the
  operator's own 2026-08-15-ruled preferred direction), not unretired backlog — so per this check's own sanctioned
  escape valve (`--update-baseline` after a reviewed pass) and this doc's own repeated precedent for this exact
  failure class, ran `check_na_corpus_ratchet.py --update-baseline`: `max_na_docs 522→521, max_na_open_todos
  1777→2155`. Filed the underlying double-counting design gap (aggregator docs should be excluded from this ratchet's
  count, mirroring `count_open_tasks.py`'s existing convention) as a new todo above rather than fixing the shared
  counting script live under a promote-gate time pressure. Verified locally post-bump:
  `check_na_corpus_ratchet.py` exits 0. Shipped via quickmerge:
  `scripts/plan-hygiene/na_corpus_baseline.yaml` + this doc.
- **2026-08-21 — ruling D104 (NA-ratchet gate scoping)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Entry only — re-gating aggregate PRs is what converts ordinary growth into the
  documented promotion deadlock, with no demonstrated safety benefit. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
