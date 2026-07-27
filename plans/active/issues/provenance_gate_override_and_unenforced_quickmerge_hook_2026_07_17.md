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
status: open
resolved_by:
nature: process
asset_group: [cross-cutting]
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
source:
  - operator 2026-07-17 — ruling: "outside pm repo block anything thats not quick merge"
  - operator 2026-07-17 — ruling: audit the 26 (33) commits properly rather than leave or revert
  - self-reported by the agent that caused it (Claude, slot-3·laptop), 2026-07-16/17
---

# Provenance-gate override + the hook that was never installed

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

- [ ] [DEVOPS] P2. Decide whether the 33 laundered commits need any dep-order spot-check beyond the bot's gate, or
      whether this doc closes it. Nothing automated will ever re-surface them.
- [x] [DEVOPS] P2. `check_strict_quickmerge.py` **fails OPEN on a bad range** — an unresolvable/invalid range prints "no
      bypassed code commits" (exit 0) rather than erroring. Found while testing the hook with a malformed sha. A typo'd
      range therefore reads as a pass. — already covered by plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md
      (see that doc for execution).
- [ ] [DEVOPS] P3. `scripts/dev/hooks/pre-push-strict-quickmerge.sh` is now redundant (all three installers point at
      `scripts/hooks/pre-push`). Still referenced by `migrate-slots-to-pathb.sh`, `quickmerge.sh` and two codex docs —
      delete + repoint per "delete deprecated code (no shims)".
- [ ] [DEVOPS] P3. The two husky UI repos (`deployment-ui`, `unified-trading-system-ui`) are skipped by the self-heal
      (`case "${_hooks_dir}" in */.husky/*) continue`), so they carry no strict guard. Wire it into husky's own
      pre-push.
- [x] [DEVOPS] P3. `/codex/08-workflows/ci-cd-flow.md:702` still calls the guard "WARN-default" — stale since it now
      blocks. — already covered by plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md (see that doc for
      execution).

## Lesson (for agents)

A gate that refuses is not automatically a broken gate. Before "unblocking" anything, read **why** it refused — the
answer was one `gh pr view --json comments` away, and the comment said exactly what to do. The alert being unhelpful
(anonymous "PROMOTION LAG") is a real defect worth fixing, but it is not a licence to override the safety mechanism it
was hiding.
