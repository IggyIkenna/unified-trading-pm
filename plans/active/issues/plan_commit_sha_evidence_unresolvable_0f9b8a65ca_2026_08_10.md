---
doc_type: issue
title:
  "PM plan-commit-sha-evidence ratchet RED: slot-28's plan cites unified-trading-pm@0f9b8a65ca which does not exist on
  any ref / on GitHub"
summary:
  "check_plan_commit_sha_evidence.py flags 1 unresolvable citation (baseline 0 -> 1):
  plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md:250 cites
  `unified-trading-pm@0f9b8a65ca` (in a `- [x] ✅ [DOCS] P1` todo's evidence) but the commit is not reachable from any
  local ref, not present after `git fetch`, and 404s on GitHub (`gh api repos/.../commits/0f9b8a65ca` -> Not Found). The
  flip commit `b9d9725354` (slot-28, 2026-08-10 11:15) introduced the citation. This red blocks every PM ship (post-gate
  failure in quality-gates.sh)."
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, plan-hygiene, ratchet, evidence, commit-sha, qg-red]
related: [/plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md]
created: 2026-08-10
author: slot-20 (infra worker)
parent_epic: plan_hygiene_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
archive_exempt: true
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: slot-20 QG pass on unified-trading-pm, 2026-08-10
---

# plan-commit-sha-evidence ratchet RED — unresolvable `unified-trading-pm@0f9b8a65ca`

## What I found

`check_plan_commit_sha_evidence.py` (PM post-gate in `quality-gates.sh`) reports 1 unresolvable `<repo>@<sha>` citation
vs a baseline of 0:

- **plan**: `plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md:250`
- **citation**: `unified-trading-pm@0f9b8a65ca` — appears in a `- [x] ✅ [DOCS] P1` todo's evidence line ("make
  `contradicted_by` and `description` REQUIRED, add `doc_line` / … `unified-trading-pm@0f9b8a65ca`")
- **introduced by**: commit `b9d9725354` ("docs(plans): flip item 3 (unified-trading-pm@0f9b8a65ca)", slot-28,
  2026-08-10 11:15), already on `origin/live-defi-rollout`.

Verification that the citation is genuinely unresolvable (not a local-clone lag):

- `git cat-file -e 0f9b8a65ca` → not present in local clone.
- `git fetch origin` then re-check → still not present.
- `gh api repos/ikennaigboaka/unified-trading-pm/commits/0f9b8a65ca` → **HTTP 404 Not Found** (the commit does not exist
  on GitHub at all).
- No local ref contains it (`git branch -r --contains` empty).

## Why it matters

`plan-commit-sha-evidence` is a blocking post-gate: while this citation is unresolvable, EVERY unified-trading-pm QG run
exits non-zero and the `.n_sha` sentinel is not written — blocking any unrelated PM ship (including pure `scripts/` +
codex changes) fleet-wide until the citation is corrected or the ratchet re-baselined. It is also a review-blocking
plan↔codex/evidence-hygiene violation on its own (per `plans/PLAN_FORMAT.md` § 8c, a `- [x]` completion MUST cite a
real, reachable commit).

## Recommended decision

Fix the citation (the owning worker / operator) rather than re-baselining the ratchet: either (a) the real commit sha
that the flip intended (slot-28's plan work) — replace `0f9b8a65ca` with the actual reachable sha, or (b) if the
evidence line cannot cite a real commit, reword the todo to remove the `<repo>@<sha>` citation. Re-baselining
(`--baseline-write`) is the LAST resort after confirming pre-existing debt; it would permanently mask the class the
check exists to catch.

## Todo

- [x] ✅ [INFRA] P1. **Fix the unresolvable `0f9b8a65ca` citation in
      `blocked_question_payload_quality_and_condition_retirement_2026_08_10.md:250`** — replaced with the real reachable
      commit sha `034cb4e2ad` by `5f5654c90e` (18th dispatch agt-e56165). Ratchet verified green: 2725 citations, 0
      unresolvable. — unified-trading-pm@5f5654c90e (repo: unified-trading-pm)

## Progress Log

- **2026-08-10 (slot-19, data_engineering worker adopting infra role)**: Citation already fixed by commit `5f5654c90e`
  (18th dispatch agt-e56165) which replaced `0f9b8a65ca` with `034cb4e2ad` in the target plan. Ratchet verified green:
  2725 citations, 0 unresolvable. Flipped the sole todo ✅. `archive_exempt: true` is TEMPORARY — per RULES.md §2's
  "never combine the checkbox flip with a git mv archival in ONE commit", the archive will be a separate follow-up
  commit immediately after this one.
