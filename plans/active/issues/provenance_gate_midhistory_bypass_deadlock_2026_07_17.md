---
doc_type: issue
title:
  The strict-quickmerge provenance gate deadlocks a MID-HISTORY bypass — neither stated remedy (re-ship / revert) can
  clear it; added an explicit re-provenance path
summary: |
  The provenance gate I installed 2026-07-17 correctly BLOCKS the LDR→main promote when a source
  commit reached live-defi-rollout without going through quickmerge. But for a bypass that is NOT the
  branch tip, neither remedy the alert named worked: it cannot be trailer-stamped without rewriting a
  shared branch, it never becomes `_on_promoted_tip` (the promote it would ride is blocked BY it),
  `git revert` leaves the sha in-range and only ADDS a violation (proven), and a content-identical
  `quickmerge --files` is a no-op. A legitimate green fix (instruments-service 19ae5890) wedged
  promotion. Fixed by adding an explicit, auditable RE-PROVENANCE path: an empty, provenanced commit
  that names the bypass in a `Reprovenance: <sha>` trailer forgives it. Gate rule + tests +
  `reprovenance_bypass.sh` shipped; a bare (non-provenanced) commit cannot self-forgive.
status: resolved
resolved_by: unified-trading-pm gate rule (_collect_reprovenanced) + scripts/cicd/reprovenance_bypass.sh
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, provenance, promotion, governance, deadlock]
related:
  [
    provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md,
    ../../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  - operator 2026-07-17 — chose "fix the gate so re-ship actually works" over a one-time hand-arm
  - measured during the 2026-07-17 instruments-service promotion-lag triage
---

# The provenance gate deadlocks a mid-history bypass

## What happened

instruments-service's LDR→main promote paged `⛔ BLOCKED by the provenance gate` (the marker + text I added this
morning). The blocker: **`19ae5890`** ("fix(sports): capture fixture round from the raw af_response", slot-3) — a real,
v2-green fix that was **direct-pushed to live-defi-rollout without quickmerge**. It touched
`instruments_service/engine/orchestrator/{__init__,sports}.py` and sat **4 commits deep**, not the tip.

## Why the stated remedies could not clear it

`check_strict_quickmerge.commit_violates` clears a source commit only via: a `Quickmerge:` trailer, `_on_promoted_tip`
(reachable from origin/main|staging), bot/`[skip ci]` author, merge commit, or no-source (carve-out). For a mid-history
bypass **none is reachable**:

- **Trailer** — can only be added by rewriting the commit (`rebase`); BANNED on a shared branch, and it is not even the
  tip so `quickmerge --files`'s amend-HEAD path does not touch it.
- **`_on_promoted_tip`** — it becomes reachable from main only when a promote MERGES; the promote is BLOCKED by it.
  Circular.
- **Revert** — PROVEN in a scratch worktree: `git revert 19ae5890` leaves 19ae5890 in `rev-list marker..LDR` AND adds
  the revert commit as a SECOND violation. Worse, not better.
- **Re-ship** — the content is already committed; `quickmerge --files` sees the paths clean and HEAD already trailer'd →
  no-op, pushes nothing. 19ae5890 stays flagged.

So the alert's own remedy text ("re-ship via quickmerge or revert") was **untrue for a mid-history bypass**. The only
mechanical clear was merging the promote PR by hand — the exact "hand-arm" the operator forbade (it launders the bypass
past the provenance baseline; see `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`).

## The fix — an explicit, auditable re-provenance path

A source commit is now ALSO forgiven if a LATER commit in the range carries a `Reprovenance: <sha>` trailer AND is
itself provenanced (`Quickmerge:` trailer / bot / `[skip ci]`). `check_strict_quickmerge._collect_reprovenanced`
computes the blessed set; `commit_violates` takes it.

- **Auditable**: the blessing commit names exactly the sha it forgives.
- **Not forgeable**: a bare (non-provenanced) `Reprovenance:` commit does NOT bless — pinned by
  `test_bare_reprovenance_commit_cannot_self_forgive`. A bypasser cannot self-clear.
- **Scoped**: a blessing for sha A does not forgive an unrelated bypass B
  (`test_reprovenance_only_forgives_the_named_sha`).
- **Equivalent to re-ship**: `scripts/cicd/reprovenance_bypass.sh <sha> --push` runs the dep-alignment gate (the
  quickmerge STAGE-1 guarantee) BEFORE creating the empty blessing commit, so the dep-provenance the gate exists to
  enforce still holds — applied to content already on green LDR. The empty commit touches no source, so it is a
  carve-out and pushes past the pre-push hook.

## Applied

`reprovenance_bypass.sh 19ae5890 --push` on instruments-service → gate clean → promote unblocked. (Filled in with the
landing sha + promote PR when it merges.)

## Follow-ups

- [ ] [DEVOPS] P2. The LDR→main fleet-bot comment (`ldr-to-main-promote-fleet.yml`) still names only "re-ship via
      quickmerge or revert". Add the mid-history `reprovenance_bypass.sh` path there too (the lag-monitor alert text is
      already updated).
- [ ] [DEVOPS] P3. Codex `codex/08-workflows/ci-cd-flow.md` § "D1 provenance gate" should document the re-provenance
      remedy so it is discoverable outside the alert.
- [ ] [DEVOPS] P3. Root prevention: the direct code push that created 19ae5890 should have been blocked by the pre-push
      hook — confirm the hook is installed in the slot clone that pushed it (the 2026-07-17 rollout covered
      main-workspace clones; per-slot `.tabs/` coverage is via setup-tab-worktrees.sh). If an agent used
      `git push --no-verify`, that is the real leak.
