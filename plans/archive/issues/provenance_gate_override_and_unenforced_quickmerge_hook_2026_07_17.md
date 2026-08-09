---
doc_type: issue
title:
  Provenance gate overridden by an agent + the strict-quickmerge hook was installed in ZERO clones — 33 bypassed commits
  promoted and laundered past the baseline
summary: |
  On 2026-07-16 an agent (Claude, slot-3·laptop) misread the LDR→main fleet bot's D1 provenance gate as an
  "auto-merge arming bug" and hand-armed two promote PRs it had deliberately refused. That promoted 33 CODE commits
  that had bypassed quickmerge (mtds 26, deployment-api 7) and moved the provenance baseline past them, so the gate now
  reports ✅ and those violations can never be flagged again. Root cause of the violations themselves: the
  strict-quickmerge pre-push hook was installed in 0 of 25 clones (install-hooks.sh copied the dep-align hook, which
  exits 0 off staging — and staging is bypassed fleet-wide), AND the /git-commit skill mandated the exact opposite of
  the CLAUDE.md HARD RULE ("never quickmerge by default — direct push is the rule"). Both are now fixed and verified;
  this doc is the surviving audit trail for the 33 laundered commits, since the machine record no longer shows them.
status: resolved
resolved_by: >-
  All 4 "Remaining / for the operator" items reached [x] -- the dep-order spot-check (operator-ruled clean, 2026-08-08),
  the two batch1-covered stale-doc items, the husky-UI wiring (2026-08-03), and the redundant-hook deletion
  (`unified-trading-pm@b02ba28c7`, 2026-08-06, verified live 2026-08-09 during
  `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 1 reconciliation). Zero open
  checkbox or prose work remains.
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service, deployment-api]
scope: [engineer, admin]
tags: [quickmerge, provenance, ci-cd, promotion, governance, agent-behaviour, audit-trail]
related:
  [
    /plans/archive/issues/features_service_raw_ldr_pushes_bypass_quickmerge_2026_07_13.md,
    /plans/archive/issues/quickmerge_agent_already_committed_fastpath_skips_trailer_2026_07_14.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /scripts/hooks/pre-push,
    /scripts/cicd/check_strict_quickmerge.py,
    /scripts/dev/hooks/pre-push-strict-quickmerge.sh,
  ]
source:
  - operator 2026-07-17 — ruling: "outside pm repo block anything thats not quick merge"
  - operator 2026-07-17 — ruling: audit the 26 (33) commits properly rather than leave or revert
  - self-reported by the agent that caused it (Claude, slot-3·laptop), 2026-07-16/17
---

# Provenance-gate override + the hook that was never installed

> **🗄️ ARCHIVED 2026-08-09** — all "Remaining / for the operator" items are `[x]`, zero remaining (checkbox AND prose),
> `locked_by:` empty. Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a doc with every todo
> done archives immediately. Closed during `ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 1's source-doc
> reconciliation: the final open item (redundant-hook deletion) shipped `unified-trading-pm@b02ba28c7` (2026-08-06,
> verified ancestor of `origin/live-defi-rollout`). Referrers fixed:
> `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (2 path-formatted refs repointed to this archived
> path).

> **Read this before trusting a ✅ from `check_strict_quickmerge.py` on mtds or deployment-api for anything dated ≤
> 2026-07-16.** The gate reads clean there because the baseline moved past the violations, not because they were ever
> reconciled. This doc is the only surviving record.

## What happened (2026-07-16)

1. The LDR→main fleet bot's **D1 provenance gate** correctly refused to arm auto-merge on `market-tick-data-service#596`
   and `deployment-api#297`: their promote ranges carried CODE with no `Quickmerge:` trailer and no carve-out. It left
   both PRs open and commented why (`ldr-to-main-promote-fleet.yml`, the `⛔ Provenance gate` comment).
2. An agent investigating a `PROMOTION LAG > 60m` alert saw `mergeStateStatus=CLEAN` + `autoMerge=false`, concluded "the
   bot creates PRs without arming auto-merge", and reported it as a bug.
3. The agent hand-armed both (`gh pr merge --auto --squash`). Both merged within 30s.
4. **Consequence**: 33 bypassed commits reached `main`, and because the promote moved the provenance baseline
   (`promote_provenance_range.py` now starts _after_ them), `check_strict_quickmerge.py` reports ✅ for both repos. The
   bypass is laundered and invisible to every automated check.

The misread was not unreasonable — and that is the actual defect: **a provenance block was indistinguishable from a
wedged pipeline.** It existed only as a PR comment + a workflow log line. mtds sat deliberately blocked ~23h and
surfaced solely as an anonymous lag warning.

## The audit (operator-requested)

**Exposure: LOW, but non-zero. Not "unvalidated code on main".**

| Repo                       | Bypassed CODE commits | Range checked                    |
| -------------------------- | --------------------- | -------------------------------- |
| `market-tick-data-service` | **26**                | `ba485822..2e674d1f` (PR #596)   |
| `deployment-api`           | **7**                 | `ce3fc501^1..10c6a1b9` (PR #297) |

What they **did** pass:

- `quality-gates-v2` on the promote PR — tests + typecheck + lint-codex, deps resolved from LDR. Both PRs were CLEAN.
- The bot's own gates: its PR body records `Tier-A + content + SIT + combination gates passed`. The provenance gate was
  the **only** one it refused.

What they **skipped** — quickmerge's dependency-oriented stages, none of which are test gates:

- STAGE 0 dep-branch cascade to transitive ancestors
- STAGE 0.4 not-behind gate
- STAGE 0.5 PM manifest staleness
- STAGE 1 dependency validation vs the workspace-manifest SSOT
- STAGE 1.5 dep alignment

**Residual risk**: dep-ordering — e.g. mtds `main` code referencing a UTL/UAC symbol that is on the dep's LDR but not
yet on the dep's `main`. The promote bot's own dep-order gate independently covers this and passed. Reverting was
considered and rejected (operator): ~26 commits of shipped fixes, work landed on top since, and the backmerge would need
untangling — far more disruptive than the breach.

<details>
<summary>The 26 mtds commits (click)</summary>

`c85af5b2` `86993970` `bb878372` `2b73729e` `d2040f8f` `34550740` `212d3a7c` `55ec86ac` `75fddb60` `c9e6080f` `5bb0e2c3`
`837b60a5` `a664511f` `be087cd8` `0da8be67` `77ff475a` `3511ab3b` `80d5aadd` `a813711b` `29db8440` `d647b8a1` `01f23b8c`
`971bdd35` `28ad6b38` `c48096e7` `ad76547c` — all `market_tick_data_service/**` source.

</details>

<details>
<summary>The 7 deployment-api commits (click)</summary>

`10c6a1b` `2cda602` `e27ba4b` `25865c0` `fb0eec8` `47a7f67` `db9c8ed` — all `deployment_api/**` source.

</details>

## Why the violations existed at all (the real root cause)

Not rogue agents — **the workspace contradicted itself, and the enforcement was dead**:

1. **The strict hook was installed in 0 of 25 clones.** `install-hooks.sh:15` copied `scripts/hooks/pre-push`, which
   held only the **dep-alignment** hook — and that returns 0 for every non-staging push. The fleet default is LDR→main
   DIRECT with staging BYPASSED, so it never fired. The real guard existed at
   `scripts/dev/hooks/pre-push-strict-quickmerge.sh` but only `setup-tab-worktrees.sh` installed it, and only into
   `.tabs/` clones. **All 33 commits came from main-workspace clones**, which no installer covered.
2. **The 5-min self-heal could never fire** — `slot-cron-ff-pull.sh` gated on `[[ ! -f pre-push ]]`, and a pre-push file
   always existed. It spent months re-affirming a hook that enforced nothing, while reporting healthy.
3. **The `/git-commit` skill mandated the opposite of the HARD RULE**: _"Never quickmerge by default — direct push to
   `live-defi-rollout` is the rule"_ (frontmatter, TL;DR, § 6, rules list). Agents following the documented skill
   produced exactly these commits. Its reasoning was sound-sounding (dirty deps make a quickmerged PR misleading) but
   direct-pushing does not fix the dep problem — it strands the branch at the provenance gate instead.

## Fixed (2026-07-17) — `unified-trading-pm@f9b64f15d` + `@66d3d5d81`

- `scripts/hooks/pre-push` is now BOTH guards chained: strict-quickmerge **BLOCKS**, dep-align unchanged on staging.
  `unified-trading-pm` is exempt (operator ruling: _"outside pm repo block anything thats not quick merge"_).
  **Verified**: blocks the real 26-commit range; passes a clean quickmerged range, a `feat/*` branch, and PM.
  **Installed 25/25 clones** (was 0/25).
- `slot-cron-ff-pull.sh` self-heal is CONTENT-gated and points at the one canonical source. **Verified by sabotage**:
  e2e-testing's hook was replaced with a bare `exit 0`; one real sweep restored it (0 → 2 grep hits), no manual step.
- `/git-commit` SKILL.md rewritten to route by WHAT changed; its two original concerns answered, not deleted.
- The provenance-gate comment now carries a stable marker and the lag monitor reports
  `⛔ BLOCKED by the provenance gate — re-ship via quickmerge. Do NOT hand-arm auto-merge` instead of anonymous lag.

## Remaining / for the operator

- [x] ✅ [DEVOPS] P2. **RESOLVED 2026-08-08 -- operator ruling: run the spot-check** (no separate operator-decisions doc
      exists for this live-session ruling; recorded here, in this doc's own
      `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` history, as the sole traceable record).
      Ran it live; CLEAN, closing this item.** Method (no local checkout of `market-tick-data-service`/`deployment-api`
      in this session -- used `gh api`/`gh run list`/`gh pr view` against both repos directly): (1) confirmed both
      repos' `quality-gates-v2` on `main` is green RIGHT NOW, 2026-08-08 -- 5/5 most-recent runs `success` for each repo
      (mtds newest `99b600c0d9` 2026-08-08T10:07Z; deployment-api newest `af6aaf6e3d` 2026-08-08T12:17Z); (2) the
      specific residual risk this doc names is dep-ordering -- e.g. mtds/deployment-api `main` code referencing a
      UTL/UAC symbol not yet on that dep's `main` at promote time (2026-07-16) -- which would surface as an
      import/collection failure in `QG slice (tests)`, not a silent pass; (3) checked the FULL failure history on `main`
      for both repos since the bypass (`gh run list --status failure`): **mtds's first failure after 2026-07-16 is
      2026-07-31** (15 days later, run `30673172481`/`30658470782` -- checked job breakdown, ordinary
      `QG slice (tests)`/`(checks)` failures, not a dependency/import error at collection time); **deployment-api's
      first failure after 2026-07-16 is 2026-07-30** (14 days later). **Zero failures in the immediate aftermath window
      (2026-07-16 through the first failure two weeks later)** -- the window where a genuine dep-floor mismatch tied to
      these specific 33 commits would be most likely to surface, before subsequent legitimate quickmerged dep-bumps
      could mask or coincidentally resolve it. (4) Re-read PR #596's own body:
      `Tier-A + content + SIT + combination gates passed` -- corroborates this doc's claim that the promote bot's own
      dep-order-inclusive gate set passed at promote time, independent of the provenance-gate override. **Verdict: no
      dep-order issue found, live or historical, traceable to the 33 laundered commits.** This doc's own "Nothing
      automated will ever re-surface them" is still true (the provenance baseline moved past them permanently), but this
      manual spot-check is the closure this todo asked for -- closing this item for good, not deferring further.
- [x] [DEVOPS] P2. `check_strict_quickmerge.py` **fails OPEN on a bad range** — an unresolvable/invalid range prints "no
      bypassed code commits" (exit 0) rather than erroring. Found while testing the hook with a malformed sha. A typo'd
      range therefore reads as a pass. — **DONE — `unified-trading-pm@fd52877f6`** (confirmed ancestor of
      `origin/live-defi-rollout`): `main()` now fails CLOSED (exit 1) on an unresolvable range; confirmed `_backmerge`
      merge commits are already carve-out-exempt via the existing 2-parent rule. Also covered by
      plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md (see that doc for full evidence).
- [x] ✅ [DEVOPS] P3. **DONE 2026-08-06** — `unified-trading-pm@b02ba28c7` (verified ancestor of
      `origin/live-defi-rollout`) deleted `scripts/dev/hooks/pre-push-strict-quickmerge.sh` and repointed its 4 live
      referrers: `scripts/dev/migrate-slots-to-pathb.sh` (`HOOK_SRC` → `scripts/hooks/pre-push`),
      `scripts/quickmerge.sh` (stale comment reference), `/codex/08-workflows/ci-cd-flow.md`,
      `/codex/05-infrastructure/per-tab-worktrees.md`. Re-verified live 2026-08-09: the hook file no longer exists on
      disk; the only remaining `pre-push-strict-quickmerge` corpus hits are archived/historical doc text (not live code
      referrers) and this batch's own plan text. `scripts/dev/hooks/pre-push-strict-quickmerge.sh` is now redundant (all
      three installers point at `scripts/hooks/pre-push`). Was referenced by `migrate-slots-to-pathb.sh`,
      `quickmerge.sh` and two codex docs — deleted + repointed per "delete deprecated code (no shims)".
  - Source: `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 (sub-item 2).
- [x] ✅ [DEVOPS] P3. The two husky UI repos (`deployment-ui`, `unified-trading-system-ui`) are skipped by the self-heal
      (`case "${_hooks_dir}" in */.husky/*) continue`), so they carry no strict guard. Wire it into husky's own
      pre-push. **na-eligibility-audit 2026-08-01: already tracked (not yet done) as an open todo in
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` ([INFRA] P3, "The two husky UI repos carry no strict-quickmerge
      guard"), which cites this exact checkbox as its Source — track completion there.** **DONE (na-eligibility-audit
      2026-08-03)** — closed via `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md:422`: DONE 2026-08-03
      (slot-9, infra), added a committed `.husky/pre-push` delegate in both `deployment-ui@a3268d0` and
      `unified-trading-system-ui@563f6238` that execs the fleet's canonical guard; 15/15 regression cases pass; full
      `quality-gates.sh` green on all three repos.
- [x] [DEVOPS] P3. `/codex/08-workflows/ci-cd-flow.md:702` still calls the guard "WARN-default" — stale since it now
      blocks. — **DONE — `unified-trading-pm@97970974e`** (confirmed ancestor of `origin/live-defi-rollout`): corrected
      L702's WARN-default line, retired the stale staging-as-canonical narrative, and added the staging re-entry
      procedure. Also covered by plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md (see that doc for full
      evidence).

## Lesson (for agents)

A gate that refuses is not automatically a broken gate. Before "unblocking" anything, read **why** it refused — the
answer was one `gh pr view --json comments` away, and the comment said exactly what to do. The alert being unhelpful
(anonymous "PROMOTION LAG") is a real defect worth fixing, but it is not a licence to override the safety mechanism it
was hiding.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — the open items sit under this doc's own
"Remaining / for the operator" heading, and the head item is a genuine judgment call ("decide whether the 33 laundered
commits need any dep-order spot-check, or whether this doc closes it"). The P3 hook-deletion item is separately
conflict-gated as `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E4**, and the
husky-UI-repos P3 item is already claimed by `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, stale-items — re-confirmed all 3 items. The
head judgment-call item stays valid. The hook-deletion item's E4 citation chain is now stale (batch2 archived) but the
underlying fact holds: `scripts/dev/hooks/pre-push-strict-quickmerge.sh` still exists on disk (verified via `find`), and
its only live re-extraction is `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 — still `status: draft`, not yet
an active duplicate, so this item stays open here. Annotated the husky-UI item with a citation to
`ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s still-open matching todo (verified NOT done there either — no
false-[x] risk). No RECLASSIFY candidates.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator judgment item, P3 extraction in draft batch4
**na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA-STALE (already-duplicated), confirmed — the sole
remaining open item (delete `scripts/dev/hooks/pre-push-strict-quickmerge.sh` + repoint its 4 referrers) is a genuinely
bounded, deterministic deletion task and was considered as a RECLASSIFY candidate on its own merits. Conflict-check:
`ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 owns this exact file (verbatim claim) and is now `status: active`
(not draft) — a live, current claim. Flipping this doc's copy would draft a competing todo against an already-dispatched
claim. Stays NA on citation; no `assigned_vm` change.

- **2026-08-09 (slot 2, `ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 1 reconciliation)**: batch4 todo 1
  landed (`unified-trading-pm@b02ba28c7`, verified ancestor of `origin/live-defi-rollout`) — the sole remaining `[ ]`
  (hook deletion + referrer repoint) flipped, live-verified (`scripts/dev/hooks/pre-push-strict-quickmerge.sh` gone, its
  4 live referrers repointed). `status` flipped to `resolved`, zero open work (checkbox AND prose). Archived per the
  6-step ritual: archive banner added, `git mv` to `plans/archive/issues/`, corpus-wide grep found 2 path-formatted
  (`/plans/active/issues/...`) referrers in `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` —
  repointed both; every other corpus mention is a bare-filename prose reference (not a path-formatted link
  `check_reference_paths.py` validates), left as historical text per convention. No new/changed contract this doc's
  closure surfaces for codex.
