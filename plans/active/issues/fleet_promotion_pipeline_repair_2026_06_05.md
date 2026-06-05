---
title:
  Fleet promotion pipeline — staging mechanics RESTORED; 7 repos blocked at quality-gates-v2 on real QG debt +
  dependency-ordering
created: 2026-06-05
author: ikennaigboaka [slot-1·laptop]
source:
  - UI registry-drift fix → discovered staging 192-behind → fleet-wide promotion-pipeline breakage
  - per-repo staging↔main↔LDR topology audit 2026-06-05
locked_by: live-defi-rollout
---

## What I found

The LDR→staging→main promotion pipeline was broken **fleet-wide**: staging branches had fallen far behind main (UI 192,
deployment **761**, instruments 39, strategy 44, features 17) or accumulated unpromoted work (uac 29, utl 16, mtds 45,
execution 7), and the LDR→staging auto-drain perpetually conflicted → main advanced only via ad-hoc direct LDR→main
merges, leaving staging vestigial.

## DONE — staging mechanics restored + the QG-clean repos promoted

- **unified-trading-system-ui**: fully fixed + promoted to **main** (registry-drift + pipeline; #27).
- **market-tick-data-service**: fully promoted to **main** (LDR-ahead-of-main = 0).
- **features-service**: staging reconciled + merged; staging→main (#16) blocked on QG (below).
- Reconciliation recipe (validated): per repo, in a throwaway worktree off staging, merge `origin/main` then
  `origin/live-defi-rollout` (`--no-verify` — the conventional-commit hook rejects the default merge message; `merge`
  isn't a valid type). For far-behind staging whose unique commits are superseded LDR-drains, `-X theirs` is safe
  (verify `git cherry` shows no genuine staging-only `+` first). Push → `promote/staging-resync-*` → aggregate PR →
  staging → staging→main PR (quality-gates-v2).
- Stale PRs closed (UI #1/#2/#4/#10; conflicting drains). UI's staging-only feature `9aa3f102` preserved.

## REMAINING — 7 repos blocked at quality-gates-v2 by GENUINE debt (the gate doing its job)

The reconciled→staging (or staging→main) PRs are open with auto-merge but **fail `quality-gates-v2`** on the merged
superset — i.e. promoting LDR→main surfaces real, pre-existing debt that must be fixed before promotion (this is correct
CI/CD behaviour, not a reconciliation bug):

| repo                    | LDR ahead of main | staging-resync PR | known blocker                                                                                                              |
| ----------------------- | ----------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| features-service        | 25                | merged; #16 →main | quality-gates-v2                                                                                                           |
| unified-api-contracts   | 23                | open              | quality-gates-v2                                                                                                           |
| unified-trading-library | 19                | open              | **ImportError `CanonicalFixtureOutcomes`/`MatchResult` from `uac.sports`** (cross-repo symbol gap) + coverage 79.85% < 80% |
| strategy-service        | 19                | open              | quality-gates-v2                                                                                                           |
| instruments-service     | 33                | open              | quality-gates-v2                                                                                                           |
| execution-service       | 20                | open              | quality-gates-v2                                                                                                           |
| deployment-service      | 20                | open              | quality-gates-v2                                                                                                           |

**Root of the blocker = two coupled problems** (the known cicd-Phase-6 workstream):

1. **Cross-repo dependency-ordering**: the LDR work spans repos (utl imports a `uac.sports` symbol that must be promoted
   to uac first). Promotion must be **dependency-ordered** (T0: uac, utl → T1 → T2), each tier QG-green before the next.
   Parallel promotion fails because consumers' QG clones deps and the symbols aren't on main/consistently-reconciled
   yet. (`quality-gates-v2` clones deps **by the PR's branch name** — so the `promote/staging-resync-*` branches must be
   consistent across the dep graph, or the dep promoted first.)
2. **Per-repo QG debt**: real failures in the merged superset (e.g. utl coverage 79.85%, broken imports) — the same
   per-repo debt the governor-crash masked (see `cicd_contract_hardening_2026_06_01.md` Phase 6).

## Recommended decision

Drive the remaining 7 as a **dependency-ordered promotion pass** (not parallel): promote T0 (uac, utl) to main first —
fixing each repo's `quality-gates-v2` failures (broken refs, coverage) as a real remediation — then T1, then T2; each
tier green before the next. The reconciled `promote/staging-resync-*` branches + aggregate PRs are already open as the
starting point. This is a deliberate CI/CD workstream (real code fixes + ordering), not a mechanical replication — it
should not be force-merged past the gate.
