---
doc_type: issue
title: >-
  LDR→main provenance-marker computation is corrupted for every repo whose last successful promote predates the
  2026-08-05T11:24:53Z security-driven git history rewrite — instruments-service, unified-trading-library,
  market-data-processing-service, AND alerting-service are stuck in a closed/superseded promote-PR loop with NO merge
  since the rewrite (alerting-service confirmed 2026-08-06, ~4h after this doc was first filed — this is actively
  blocking a live production fix from reaching the running service, not just a hygiene concern)
summary: >-
  Discovered while investigating why instruments-service PR #1084 (the DP-CATALOG-001 sports-catalogue fix, `497c4f5e`)
  was closed by the provenance gate — see
  `instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md`. `497c4f5e` itself is NOT a violation
  (it carries a proper `Quickmerge: agent` trailer). Live-running `check_strict_quickmerge.py` locally over the PR's own
  base..head range (`origin/main..497c4f5e`, i.e. what the checker falls back to) found 19 REAL, unrelated foreign
  bypass commits (other agents' sports/cefi/defi work, 2026-08-05/06, no `Quickmerge:` trailer, not carve-outs) — a
  genuine, if separate, accumulation. But that is not the range production actually uses: `promote_provenance_range.py`
  computes a "since-last-promote MARKER" range (the `headRefOid` of the last MERGED `chore(promote)`-titled PR into
  `main`), and only falls back to `origin/main..LDR` if that marker SHA is unresolvable. For instruments-service the
  marker is `0247912d` (PR #1080, merged 2026-08-05T06:48:16Z — BEFORE the rewrite). `promote_provenance_range.py`'s
  `commit_reachable()` only checks that the marker SHA exists as a git object (via a best-effort `git fetch <remote>
  <sha>`, which GitHub still serves) — it does NOT verify the marker is an actual ANCESTOR of the current (rewritten)
  `live-defi-rollout`. Live-verified: `git log 0247912d..origin/live-defi-rollout` returns **3,701 commits**, with the
  OLDEST being `fbfc34af` — the repo's Nov-2025 INITIAL commit. This is the unmistakable signature of a marker that sits
  on the pre-rewrite history line, with essentially no useful common ancestor against the post-rewrite line — the range
  balloons to nearly the entire repo history, most of which predates the `Quickmerge:` trailer convention itself
  (codified 2026-06-08) and would false-positive as "bypassed quickmerge" content that is, in reality, already on `main`
  from months ago. Cross-checked 5 repos affected by the same 2026-08-05T11:24:53Z rewrite (evidenced by each one's
  `<repo>.stale-pre-history-rewrite-20260805T112453Z` sibling clone, itself downstream of the archived secret-leak
  remediations `plans/archive/issues/gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md` /
  `github_pat_in_instruments_service_env_2026_05_15.md`): the 3 whose last successful main-promote predates the rewrite
  (instruments-service 2026-08-05T06:48:16Z, unified-trading-library 2026-08-05T08:49:47Z,
  market-data-processing-service 2026-08-05T08:49:47Z) are ALL currently stuck in a closed/superseded promote-PR loop
  with zero merges since; the 2 whose last successful promote landed AFTER the rewrite (execution-service
  2026-08-06T10:33:04Z, e2e-testing 2026-08-06T11:06:40Z) are promoting normally right now. This is a clean,
  near-perfect correlation, not a coincidence — a repo self-heals the instant ONE promote clears (its marker then points
  at a valid post-rewrite SHA), but getting that first clean promote through is itself blocked by the very bug being
  described (a deadlock).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    instruments-service,
    unified-trading-library,
    market-data-processing-service,
    alerting-service,
    execution-service,
    e2e-testing,
  ]
scope: [engineer, admin]
tags: [ci-cd, provenance, quickmerge, ldr-main, promotion, git-history-rewrite, cross-repo]
related:
  [
    /plans/active/issues/instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md,
    /plans/archive/issues/utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md,
    /plans/archive/issues/provenance_gate_squash_perpetual_block_2026_06_17.md,
    /plans/archive/issues/provenance_gate_midhistory_bypass_deadlock_2026_07_17.md,
    /plans/archive/issues/gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-06
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "surfaced while diagnosing instruments-service PR #1084 (497c4f5e provenance-blocked), 2026-08-06"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/scripts/cicd/promote_provenance_range.py,
    unified-trading-pm/scripts/cicd/check_strict_quickmerge.py,
    unified-trading-pm/scripts/cicd/ldr_to_main_fleet_promote.sh,
  ]
---

# LDR→main provenance-marker corrupted post-history-rewrite — 3 repos stuck since 2026-08-05

## What was measured (live, 2026-08-06)

- **instruments-service PR #1084/#1085 both closed, not merged** (`superseded by newer validated SHA` — the fleet bot's
  normal churn behavior, NOT itself a failure signal). PR #1084 specifically carried the
  `<!-- promote:provenance-blocked -->` bot comment. **5 consecutive promote PRs (#1081-#1085) closed with zero merges**
  across 2026-08-06T06:35Z→11:00Z; as of 13:15Z there is **no open promote PR at all** (the fleet cron `*/15` has not
  (re-)opened one in >2h, itself worth watching).
- **`check_strict_quickmerge.py --range origin/main..497c4f5e` (the checker's OWN fallback range) → 19 real, distinct,
  unrelated foreign bypass commits**, e.g. `37c4dd20` (options_chain OPTION alias), `830e33ae` (DERIBIT instrument_id
  fix, itself dirty-deps-carve-out-flagged but missing the required trailer value), `b95574f5` (defi SPOT_ASSET
  siblings), `7b812d2e` (api_football root-cause fixes) — real, substantive, unrelated to `497c4f5e`/DP-CATALOG-001.
  None of these is `497c4f5e` itself (`497c4f5e` correctly shows `passed through quickmerge`).
- **The marker-based range production actually computes is different and far larger.** `promote_provenance_range.py`'s
  marker for instruments-service→main = `0247912d85288d35d83432d128b2ddfb399baa6b` (headRefOid of PR #1080, the last
  MERGED `chore(promote)`-titled PR, merged 2026-08-05T06:48:16Z). `commit_reachable()` does `git fetch <remote> <sha>`
  then `git cat-file -e <sha>^{commit}` — object EXISTENCE only, not ancestry. Reproduced live: the fetch succeeds
  (GitHub still serves the SHA), so the marker is treated as "reachable" and the range becomes
  `0247912d..origin/live-defi-rollout` — **3,701 commits**, oldest being the repo's Nov-2025 initial commit `fbfc34af`.
  This is not a subset relationship of the real 19; it is a vastly larger, largely-spurious range spanning almost the
  entire pre-rewrite repo history (most of which predates the `Quickmerge:` convention, codified 2026-06-08, and would
  false-flag as bypass even though its content has been on `main` for months).
- **Cross-repo correlation (all 5 repos sharing the 2026-08-05T11:24:53Z history rewrite, evidenced by each
  `<repo>.stale-pre-history-rewrite-20260805T112453Z` sibling clone on disk):**

  | repo                           | last successful main-promote | vs. rewrite (11:24:53Z) | current state                                                                                                                            |
  | ------------------------------ | ---------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
  | instruments-service            | 2026-08-05T06:48:16Z         | BEFORE                  | stuck — 5 closed PRs, 0 merges since                                                                                                     |
  | unified-trading-library        | 2026-08-05T08:49:47Z         | BEFORE                  | stuck — many closed PRs (#753-#758)                                                                                                      |
  | market-data-processing-service | 2026-08-05T08:49:47Z         | BEFORE                  | stuck — many closed PRs (#592-#597)                                                                                                      |
  | alerting-service               | 2026-08-04T21:47:27Z (#334)  | BEFORE                  | stuck — 10 closed PRs (#335-#343), 0 merges since; #344 (a live-production alerting fix, `4e252b4`) is OPEN now and blocked the same way |
  | execution-service              | 2026-08-06T10:33:04Z         | AFTER                   | healthy — merged again 10:33Z                                                                                                            |
  | e2e-testing                    | 2026-08-06T11:06:40Z         | AFTER                   | healthy — merged again 09:14Z, 11:06Z                                                                                                    |

  The 3-stuck/2-healthy split lines up exactly with pre-/post-rewrite marker timing — not a coincidence. A repo
  self-heals the instant one promote clears (new marker = a valid post-rewrite SHA), but reaching that first clean
  promote is precisely what the corrupted range blocks — a deadlock structurally identical in shape to the
  mid-history-bypass deadlock `reprovenance_bypass.sh` was built for
  (`provenance_gate_midhistory_bypass_deadlock_2026_07_17.md`), just triggered by a history rewrite instead of a raw
  bypass push, and at a much larger (thousands-of-commits) scale.

## Why this is not something I fixed autonomously

Two reasons, mirroring the UTL-34-bypass precedent
(`utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md`):

1. **The real 19-commit list (instruments-service) is foreign, substantial, multi-subsystem code** — blessing it via a
   bulk `reprovenance_bypass.sh` sweep asserts all 19 are correct and promote-ready, which I cannot verify, and the
   prior precedent was explicit that this requires either the owning agents re-shipping their own commits or a
   deliberate operator-authorized sweep, never an autonomous bulk-bless.
2. **The marker corruption is a different, code-level bug** (`commit_reachable()` checks object existence, not ancestry)
   with a much bigger blast radius (3 core repos' promotion pipelines, one of them — UTL — a near-universal fleet
   dependency). A fix here is either a `promote_provenance_range.py` code change (verify true ancestry, not just object
   existence, so a stale pre-rewrite marker correctly triggers the safe fallback range) or a manual marker-reset per
   affected repo — both are judgment calls with fleet-wide blast radius that belong to a human decision, not something
   to change unilaterally mid-way through an unrelated sports-catalogue fix.

## Options (operator decision)

- [x] [OPERATOR] P1. **Root-cause code fix (recommended)**: harden `promote_provenance_range.py`'s `commit_reachable()`
      to verify the marker is a true ancestor of `ldr_ref` (e.g. `git merge-base --is-ancestor <marker> <ldr_ref>`), not
      just that the object exists — a marker that fails ancestry should fall through to the safe `base_ref..ldr_ref`
      fallback (exactly the fallback logic that already exists and already produces the correct, reviewable 19-commit
      list for instruments-service). This fixes the current 3 stuck repos AND prevents recurrence on any future history
      rewrite. **DONE 2026-08-06** — operator-approved 2026-08-06 to proceed (root-cause fix, not tactical unblock).
      Shipped `unified-trading-pm@7b5390649` (carve-out direct push to `main`, backmerged to LDR automatically at
      `5983e96a3`). Added `marker_is_ancestor()` (`git merge-base --is-ancestor`) + `marker_usability()` composing it
      with the existing object-existence check; `resolve_range()`'s `marker_reachable` param renamed `marker_usable`. 7
      new regression tests in `tests/unit/test_promote_provenance_range.py` reproducing the exact
      reachable-but-not-ancestor scenario. Live-verified in production (see Progress Log) — the range computation is now
      CORRECT for all 4 originally-flagged repos; 3 remain blocked by genuine unrelated foreign quickmerge-bypass
      commits now correctly exposed by the fixed range (a separate, distinct issue per this doc's own precedent, not
      re-opened here), and alerting-service turned out to be blocked by an unrelated SIT-gate timing condition, not this
      bug (see Progress Log for the distinction).
- [ ] [OPERATOR] P1. **Tactical unblock in parallel**: for each of the 3 stuck repos, get exactly one clean promote PR
      merged (admin-merge after a real diff review, or resolve the underlying 19/N-commit provenance list first via
      owning-agent re-ship / operator-authorized `reprovenance_bypass.sh` sweep per repo) — the repo then self-heals
      (new marker = valid post-rewrite SHA), matching how execution-service and e2e-testing already recovered on their
      own.
- [ ] [DEVOPS] P2. Audit whether any OTHER repos have a `chore(promote)`-titled merge whose `mergedAt` predates
      2026-08-05T11:24:53Z but were not part of the 5-repo history-rewrite set — confirm this is genuinely scoped to
      exactly {instruments-service, unified-trading-library, market-data-processing-service} and not wider.

## Progress Log

- **2026-08-06** — Filed while re-shipping the DP-CATALOG-001 sports-catalogue fix for instruments-service (see
  `instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md`). `497c4f5e` was found to already be
  correctly quickmerge-provenanced — nothing to re-ship there — so the closed PR #1084 sent me looking at what actually
  blocked it, surfacing this much larger cross-repo finding. Flagged for operator decision per the established
  "bulk-bless / gate-code-change needs a human call" precedent; not fixed autonomously.
- **2026-08-06, ~4h later** — Confirmed a 4th affected repo while verifying whether a same-day production alerting fix
  (`alerting-service@4e252b43b303`, a PagerDuty-crash + email-fallback + refire-storm dedup fix) had actually reached
  the running Cloud Run service (`dp-alerting-subscriber`). It had NOT: the live revision
  (`dp-alerting-subscriber-00015-lcn`) is running an image built 2026-07-28, over a week stale. Root cause: identical
  pattern — `gh pr list` shows alerting-service's last successful `chore(promote)` merge was PR #334
  (2026-08-04T21:47:27Z, before the rewrite), followed by 10 straight closed-not-merged promote PRs (#335-#343) through
  today, and the OPEN PR #344 carrying the production fix (`4e252b4`) is checks-green (`sit-gate/fleet-green`,
  `semver-agent/label-check` both pass) but not merging — consistent with the same provenance-marker-range corruption,
  not a distinct new bug. This directly answers this doc's own P2 audit todo (partially — confirms the blast radius is
  wider than the original 3, at least one more repo affected) and raises the practical urgency: this isn't just a
  hygiene/cleanliness issue, it is actively preventing a live incident fix from reaching production. Not fixed
  autonomously, same reasoning as above.
- **2026-08-06, root-cause fix shipped + live-verified** — Operator approved proceeding with the root-cause code fix
  (not the tactical unblock). Read `promote_provenance_range.py` in full; `commit_reachable()` did
  `git cat-file -e <sha>^{commit}` only (object existence). Added `marker_is_ancestor(marker, ldr_ref, cwd)`
  (`git merge-base --is-ancestor`) and `marker_usability()` composing both checks (reachable AND ancestor,
  short-circuiting the ancestry check when unreachable); `resolve_range()`'s `marker_reachable` bool param renamed
  `marker_usable` for accuracy. 7 new tests added (`test_marker_is_ancestor_true/false`,
  `test_marker_usability_reachable_and_ancestor_is_usable`,
  `test_marker_usability_reachable_but_not_ancestor_is_unusable` — the exact regression, asserting a reachable
  non-ancestor marker composes to `resolve_range(..., marker_usable=False)` and selects the fallback range,
  `test_marker_usability_unreachable_never_checks_ancestry`, `test_marker_usability_fetches_then_rechecks_both`); 4
  renamed for the new terminology. Full `quality-gates.sh --no-fix` green in the primary LDR worktree (1732 tests
  passed, lint/type-check/codex-compliance clean; the only failure was an unrelated pre-existing
  `plan-commit-sha-evidence` ratchet regression in 3 OTHER already-committed plan docs from concurrent agents, confirmed
  via direct script run + git blame — not caused by, or touching, this change). **Shipped via the PM `scripts/**`
  direct-to-main carve-out** (`codex/08-workflows/ci-cd-flow.md` carve-out #3): confirmed
  `ldr-to-main-promote-fleet.yml`'s cron checks out PM at its DEFAULT branch (`main`, verified via
  `gh repo view --json defaultBranchRef`), so a normal LDR-first ship would not have taken effect for the cron without
  first surviving the very promotion pipeline being fixed (circular). Built the commit in a scratch worktree at
  `origin/main` tip (main and LDR were 684 commits apart — not a fast-forward target from LDR), committed
  `unified-trading-pm@7b5390649f9ddf8f6c55408b208e7e946ca13976`, pushed directly to `main` (GitHub logged an explicit
  branch-protection bypass, expected for this carve-out). The `uts-backmerge-bot` automatically merged it back into LDR
  within minutes (`5983e96a3`, "Merge remote-tracking branch 'origin/main' into `_backmerge`") — no manual LDR push was
  needed. **Live production verification** (direct reproduction + a real fleet-cron run, `gh run 31110844195`, manually
  triggered post-ship, `2026-08-06T14:27Z`):
  - **instruments-service**:
    `mode=fallback marker=0247912d… reachable=True ancestor=False → origin/main..origin/live-defi-rollout` — the exact
    bug reproduction, now correctly falling back (was the corrupted 3,701-commit marker range pre-fix).
    `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` over the corrected range found
    exactly the same 19 real foreign bypass commits already identified in this doc's original diagnosis (`37c4dd20`,
    `830e33ae`, `b95574f5`, `7b812d2e`, etc.) — RANGE COMPUTATION CONFIRMED CORRECT. PR #1088 did NOT merge in this run
    (blocked by those 19 genuine unrelated violations, exactly as this doc's own P1 "tactical unblock" option
    anticipated as a distinct follow-up — NOT attempted here, out of scope per the established bulk-bless precedent).
  - **unified-trading-library**: same pattern, live-verified in the fleet run —
    `mode=fallback marker=08e1191f… reachable=True ancestor=False → origin/main..origin/live-defi-rollout`; blocked by
    `⛔ provenance: unified-trading-library has non-quickmerge CODE on LDR` (genuine unrelated violations in the
    now-correct range, not investigated further — out of scope). PR #760 did not merge in this run.
  - **market-data-processing-service**: same pattern —
    `mode=fallback marker=6c18a1e5… reachable=True ancestor=False → origin/main..origin/live-defi-rollout`; blocked by
    the same `⛔ provenance` non-quickmerge-code message. PR #598 did not merge in this run.
  - **alerting-service — IMPORTANT CORRECTION to this doc's earlier inference**: direct reproduction shows its marker
    (`8626c70d…`, PR #334, merged 2026-08-04T21:47:27Z — BEFORE the rewrite, same as the other 3) resolves
    `reachable=True ancestor=True` — i.e. this marker was NEVER broken by the ancestry bug; alerting-service's history
    was not disconnected the way instruments-service/UTL/MDPS were. In the live fleet run it never even reached the
    provenance check — it was blocked earlier, at the SIT gate:
    `SIT GATE BLOCK alerting-service: true-delta not SIT-validated on this tree (LDR tree='a8f26e07c27d…') — fail-CLOSED. Dispatching SIT-on-LDR; a later tick promotes once SIT validates this exact tree.`
    This is a distinct, unrelated, self-resolving timing condition (LDR moved forward since the last SIT validation of
    alerting-service's tree) — NOT the bug this doc describes. The original 10-closed-PR pattern (#335-343) for
    alerting-service was therefore likely driven by this same SIT-gate/bot-churn dynamic all along, not the
    marker-ancestry bug — the earlier "4th affected repo" inference (pattern-matched from the closed-PR-loop symptom,
    not live-verified the way instruments-service was) does not hold up under direct verification. Regardless, this
    means the fix does not need to do anything further for alerting-service — it was never broken by this bug in the
    first place.
  - **Regression-safety confirmed on the healthy path**: the same live fleet run promoted 2 other repos
    (`client-reporting-api`, `batch-live-reconciliation-service`) via
    `mode=marker … ancestor=True → ✅ provenance: promote-range is quickmerge-clean … ✅ auto-merge armed` — confirms
    the fix does not break the fast, common case where the marker legitimately IS an ancestor.
  - Net: **the root-cause range-computation bug is fixed and live-verified in production, in both directions**
    (correctly falls back on a broken marker, correctly uses the marker range on a healthy one). It does not, by itself,
    merge any of the 4 originally-flagged repos — 3 were never expected to (this doc's own text: fixing the range
    computation exposes, but does not resolve, the genuine unrelated foreign-bypass backlog each now correctly shows),
    and the 4th (alerting-service) turns out not to have been broken by this bug at all. A SIT-on-LDR run was dispatched
    for alerting-service's current tree during this verification; whether it clears on a subsequent cron tick is being
    tracked separately, not as part of this bug's resolution.
