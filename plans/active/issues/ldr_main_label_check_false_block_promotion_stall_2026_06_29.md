---
doc_type: issue
title: "LDR→main promotion stall (2026-06-29) — TWO distinct causes: (A) a flaky QG dep-clone staled UTL's tier-0 ci_status (morning lag, drained); (B) the LIVE fleet promoter's SIT-rehome gate deadlocked every breaking-delta repo on a never-written sit_validated_tree, behind a chain of 6 stacked bugs. (A) and (B) are independent."
created: 2026-06-29
source:
  - .github/workflows/ldr-to-main-promote-fleet.yml
  - system-integration-tests/.github/workflows/full-workspace-sit.yml
  - scripts/cicd/detect_breaking_change.py
assigned_vm: NA
status: active
priority: P1
summary: "Two independent causes behind LDR→main not advancing. (A) MORNING LAG: a flaky QG dep-clone (phantom-version / stale-deps fallback) left unified-trading-library's tier-0 ci_status stuck FAILING while green; the dep-order gate held its dependents → >60m lag alert; cleared by re-greening UTL. (B) PERSISTENT BREAKING-DELTA STALL (verified 2026-06-29, the instruments-service class): the LDR→main fleet promoter IS live and scheduled (NOT inactive — the earlier draft was wrong), and its WS-L SIT-rehome gate fail-closes any repo with a breaking/unknown AST delta until Firestore carries a sit_validated_tree fingerprint. That fingerprint was NEVER written, behind a chain of 6 stacked bugs (SIT-stamp producer stranded off SIT's default branch → invalid YAML in that producer → differ counting private __all__ names as breaking → legacy promote/<repo> ref D/F-conflict → jammed squash-divergence backmerge). instruments-service fully resolved + promoted; features-service/deployment-ui/agent-orchestrator were on the same class."
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - unified-trading-pm
  - unified-trading-library
  - system-integration-tests
  - instruments-service
  - market-tick-data-service
  - market-data-processing-service
  - deployment-api
  - deployment-service
  - deployment-ui
  - features-service
  - agent-orchestrator
scope: [engineer, admin]
tags: [cicd, promotion, ldr-main, ci-status, flaky-qg, dep-clone, sit-rehome, sit-validated-tree, breaking-detection, promote-ref]
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-29
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **Correction #2 (2026-06-29, supersedes Correction #1):** Correction #1 claimed the LDR→main fleet promoter is
> "intentionally staged / NOT active in production" and demoted the SIT-stamp deadlock to an inactive forward note.
> **That is DISPROVEN.** `ldr-to-main-promote-fleet.yml` is on PM's default branch (`main`) and **fires on its `*/15`
> schedule** (verified: scheduled runs at 08:47, 10:24, … plus the `8,23,38,53` cron) — it is the **live** fleet
> promoter, and its SIT-rehome breaking-change gate **was the active blocker** for every repo with a breaking/unknown
> AST delta. Non-breaking repos sail through (which is why the morning backlog "drained normally" and Correction #1
> wrongly generalised). Cause (A) below (UTL flaky-QG) was a real, *separate* morning trigger; Cause (B) is the
> persistent breaking-delta stall and is the instruments-service class.

## Symptom

Slack `#ci-failures` (2026-06-29 11:11): **PROMOTION LAG > 60m — 9 branch-pairs across 8 repos un-propagated**
(`instruments-service`, `market-tick-data-service`, `deployment-service`, `market-data-processing-service`,
`deployment-api`, …). Separately, `instruments-service` stayed diverged (main↔LDR) long after the morning backlog
"drained" — the thread that exposed Cause (B).

## Cause (A) — flaky QG staled UTL's tier-0 ci_status (morning lag; verified; drained)

`unified-trading-library`'s `ci_status` was stuck `FAILING` (`qg_red_reason=pytest`) in Firestore **while the code was
green**. UTL is tier-0, so the **dep-order gate held its dependents** out of promotion → the >60m lag alert. Deeper
cause (per Ikenna's agent): the **QG dep-clone's phantom-version / stale-deps fallback flaked UTL's quality gate**. It
cleared when UTL's `quality-gates-v2` was re-run (04:41 → `MAIN_GREEN` 04:48). **Durable fix (P1): harden the flaky QG
dep-clone** — owned by Ikenna's CI/CD agent. This cause is independent of (B).

## Cause (B) — fleet promoter's SIT-rehome gate deadlocked breaking-delta repos (verified 2026-06-29; the IS class)

The LIVE fleet promoter reaches each `ldr_main` repo every ~15 min and runs a `SIT GATE` (WS-L SIT-rehome, part 2): a
repo whose `main..LDR` AST delta is **breaking/unknown** may only promote once the cross-repo SIT suite has validated
**that exact LDR tree**, proven by Firestore `sit_validated_tree == LDR tree`. For the IS class that fingerprint was
**never written**, behind a chain of six stacked bugs — each hidden behind the previous, all independently verified:

1. **SIT gate fail-closed** — IS had a breaking delta → required `sit_validated_tree`; Firestore had none (`unset`).
2. **SIT-stamp producer stranded off SIT's default branch** — the `Stamp SIT_VALIDATED + LDR tree` step (which writes
   `sit_validated_tree` via a `ci-status-update` dispatch) existed only on `system-integration-tests`'
   `live-defi-rollout`, never on its `main`. `repository_dispatch [full-workspace-sit]` always runs the **default
   branch**, so the stamp never executed. Why stranded: SIT is **not** an `ldr_main` repo, so it promotes via the
   currently-excluded **staging→main** path; its LDR was 22 ahead of main. **Fix: promoted SIT LDR→main (PRs #288/#289).**
3. **Invalid YAML in that producer** — both embedded `python3 -c` blocks sat at column 0, below the `run: |` base, so
   the whole workflow was YAML-invalid. Never caught because the producer never executed (it only ever runs on the
   default branch via dispatch). Promoting it exposed the bug ("workflow file issue" → SIT couldn't run on main).
   **Fix: re-indent both blocks (PR #289); verified YAML parses + both blocks compile after dedent.**
4. **Differ counted private `__all__` names as public API** — `detect_breaking_change.py` set `surf.exports =
   declared __all__` verbatim, so `_CEFI_VENUES`/`_TRADFI_VENUES` (underscore-prefixed, listed in `__all__`) counted as
   public exports; the venue-producer consolidation removed them → false `is_breaking=true` → (a) SIT-gate-required, (b)
   LABEL-CHECK BLOCK (`feat:` says minor, diff says breaking). These are internal-but-cross-module-shared constants, not
   cross-repo public API (SIT passed green). **Fix: filter `_`-prefixed names out of `declared_all`, consistent with
   every other branch in `extract_surface`; +regression test; PM@`da4dc099`. Real IS refs now resolve non-breaking.**
5. **Legacy `promote/<repo>` ref D/F-conflict** — the per-SHA immutable-ref scheme (`promote/<repo>/<sha>`, added
   2026-06-28) cannot create a ref when the legacy no-slash `promote/<repo>` ref still exists (git directory/file
   conflict → HTTP 422). The bot's superseded-ref cleanup only matches `promote/<repo>/` (trailing slash), so it never
   removes the legacy ref → the promoter is **permanently stuck** on any repo carrying one. **Fix (IS): deleted the
   orphaned `promote/instruments-service` ref.**
6. **Jammed backmerge / squash divergence** — `main-backmerge-to-ldr` had stuck (open conflict PR), so LDR was not a
   superset of main (main's promote-squash commit unabsorbed), violating Option-B's "LDR→main is always clean"
   precondition → the promote PR went `dirty`. main's only post-merge-base commit was the promote squash (no
   direct-to-main change), so its content is already in LDR. **Fix (IS): `-s ours` backmerge of main into LDR (keeps
   LDR's exact tree, absorbs the squash as a parent → main becomes an ancestor → clean LDR→main).**

## Resolution status

- **instruments-service: FULLY PROMOTED** — `main` tree == LDR tree (`c2abbdd82fac`), `behind_by=0` (divergence gone),
  via PR #697 (v2-gated). The SIT stamp now writes `sit_validated_tree` for all 21 covered repos; the differ resolves
  IS non-breaking; legacy ref cleared; backmerge reconciled.
- **Durable fixes live on main:** (#2) SIT producer on `system-integration-tests:main`; (#3) producer YAML repaired;
  (#4) differ private-`__all__` fix on `unified-trading-pm:main` (`da4dc099`) + regression test.
- **Cause-(A) morning backlog** drained earlier via gated manual LDR→main PRs (deployment-api, deployment-service,
  market-tick-data-service, market-data-processing-service, agent-orchestrator).
- **Sweep of the remaining Cause-B class (2026-06-29 ~13:35):**
  - **agent-orchestrator: PROMOTED** (PR #530, v2-gated; unknown-delta → label-check skipped; backmerge self-reconciled,
    `behind_by=0`). main tree == promoted snapshot `248b6c47`.
  - **deployment-ui: PROMOTED + RECOVERED** (PR #346, v2-gated; main tree == LDR tree `80e886b4`). See Bug #7 below — its
    `live-defi-rollout` was erroneously deleted by a stale promote PR's `--delete-branch`; restored to its exact last tip
    and `-s ours`-reconciled. No commits lost.
  - **features-service: HELD for operator decision** — NOT a differ bug (unlike IS). It removed a *legitimately public*
    function `extract_book_microstructure_feature_dict` under `feat:` (minor) with no `feat!:` in range → label-check
    correctly BLOCKS. Verified **zero cross-repo consumers** (grepped ml/strategy/execution/mdps/UAC/UTL) and it's on
    0.x (where `feat!`==minor, so version-neutral), so it is safe to promote — but doing so means satisfying a
    correctly-firing semver-hygiene gate by judgment. Options: (a) promote via v2-gated PR (consumer-less, version-
    neutral); (b) relabel `feat!(features): …` on LDR so the bot promotes it; (c) leave for the developer. Awaiting
    operator call; legacy `promote/features-service` ref (#5) left in place until the decision.

## Bug #7 (CRITICAL, separate hazard) — stale `head=live-defi-rollout` promote PR + `--delete-branch` deletes LDR

During the deployment-ui promote, a **stale pre-frozen-ref promote PR (#345, "manual drain", head =
`live-defi-rollout`)** still had `--delete-branch` auto-merge armed. When its `quality-gates-v2` finally went green it
auto-merged (2026-06-29 13:33:38Z) and **`--delete-branch` deleted the `live-defi-rollout` branch itself** (events:
`DeleteEvent ref=live-defi-rollout` alongside the main push). This is exactly the class the frozen-ref scheme
(`promote/<repo>/<sha>` head) was introduced to prevent — but legacy armed PRs predating it are live land-mines.

- **Recovery (done):** no commits lost — LDR's last tip (`955140892a11`, tree `80e886b4`, 04:18) was preserved in the
  frozen ref + on main. Restored `refs/heads/live-defi-rollout` to that sha, then `-s ours`-reconciled with main.
- **Fleet audit (done):** swept all 21 `ldr_main` repos — **all now have `live-defi-rollout`**, and **none** has an open
  `base=main, head=live-defi-rollout` PR with auto-merge armed. deployment-ui's #345 was the only land-mine; it has
  fired and is recovered. No remaining time-bombs.

## Durable follow-ups (P1)

- [ ] **(A) Harden the flaky QG dep-clone** (phantom-version / stale-deps fallback) — owned by Ikenna's CI/CD agent.
- [x] **(#4) Differ: exclude `_`-prefixed names from `__all__` export surface** — PM@`da4dc099` + test. DONE.
- [x] **(#3) SIT producer YAML repaired + landed on SIT main** — PR #289. DONE.
- [ ] **(#5) Harden the bot's superseded-ref cleanup** to ALSO delete the legacy no-slash `promote/<repo>` ref (the
      `startswith("promote/<repo>/")` filter misses it), so the per-SHA ref scheme can never D/F-conflict. Until fixed,
      every repo with a lingering `promote/<repo>` ref will 422 on ref creation.
- [ ] **(#6) Auto-resolve the squash-divergence backmerge** — `main-backmerge-to-ldr` should `-s ours` merge main into
      LDR when the only divergence is an unabsorbed promote-squash, instead of leaving a conflict PR open (which then
      blocks LDR→main too).
- [ ] **(#7) CRITICAL — never arm `--delete-branch` on a `head=live-defi-rollout` promote PR.** Such a PR deletes the
      SSOT branch on merge (deployment-ui hit this via stale PR #345). Mitigations: (a) the promoter already uses frozen
      `promote/<repo>/<sha>` heads — ensure NO path still opens promote PRs with `head=live-defi-rollout`; (b) add a
      guard that refuses `--delete-branch` when the head is a protected/long-lived branch; (c) sweep + close any legacy
      armed `head=live-defi-rollout` promote PRs across the fleet (done once 2026-06-29; make it a recurring check).
- [ ] **(features-service) Operator decision** — promote (consumer-less, version-neutral) vs relabel `feat!:` vs defer.

## Progress Log

- 2026-06-29 (Correction #1): over-attributed to LABEL-CHECK/SIT-stamp, then walked back to "fleet promoter inactive /
  UTL flaky-QG only." The walk-back was itself wrong about the promoter being inactive.
- 2026-06-29 (Correction #2): verified end-to-end that the fleet promoter is LIVE + scheduled and its SIT-rehome gate
  was the active blocker for the breaking-delta class. Diagnosed + fixed the 6-bug chain; promoted instruments-service
  to main (PR #697, tree-equal, behind_by=0). Recorded durable follow-ups (#4/#3 done; A/#5/#6 open).
- 2026-06-29 (sweep + Bug #7): promoted agent-orchestrator (PR #530) and deployment-ui (PR #346). Discovered Bug #7 — a
  stale `head=live-defi-rollout` promote PR (#345) with armed `--delete-branch` **deleted deployment-ui's LDR branch**
  on merge; recovered it (no commits lost) + `-s ours`-reconciled. Audited all 21 repos: all have LDR, no remaining
  armed `head=live-defi-rollout` PRs. features-service HELD for an operator semver-label decision (real public-API
  removal, but consumer-less + 0.x version-neutral). Recorded follow-up #7 (CRITICAL).
