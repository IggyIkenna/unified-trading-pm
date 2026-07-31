---
doc_type: issue
title:
  plan-commit-sha-evidence ratchet regression (23 > baseline 18) — fabricated SHA unified-trading-pm@7e0aab35f cited 5x
  across 2 unrelated docs
summary: >-
  Discovered while trying to ship an unrelated tradfi issue doc — `bash scripts/quality-gates.sh --no-fix` failed
  post-gate check `plan-commit-sha-evidence` (23 unresolvable citations > baseline 18,
  `scripts/quality_gates/check_plan_commit_sha_evidence.py`). Verified pre-existing and unrelated to my own diff
  (reproduced with my new file removed, and after a full `git pull --ff-only`). Isolated the exact 5 new violations
  (current 23 minus the 18 already in `plan_commit_sha_evidence_baseline.yaml`): all 5 cite the SAME SHA,
  `unified-trading-pm@7e0aab35f`, across `ci_satellite_ao_dispatch_batch2_2026_07_29.md:258` and 4 lines in
  `issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (162/167/170/181). `git cat-file -e
  7e0aab35f` confirms the SHA does not exist anywhere in `unified-trading-pm`'s history (checked `--all` branches). `git
  log` on the breaking_change_differ doc shows the citation landed via commit `a1dcab5f8` ("docs(plans): flip
  detect_breaking_change.py registry-data-dict blind-spot todo") — the exact fabricated-evidence class this ratchet
  exists to catch (source doc: `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`), just not yet
  caught/corrected. This is currently BLOCKING every `unified-trading-pm` commit fleet-wide under the green-tree HARD
  RULE — filed + repo-blocker declared per worker.md §4b rather than absorbing the fix into my unrelated tradfi task.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, fabricated-citation, quality-gates, repo-blocker]
related:
  [
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md,
  ]
created: 2026-07-31
parent_epic: agent_operating_framework_master
priority: P1
source: [tradfi_satellite_ao_dispatch_batch5-001, worker slot 9]
assigned_vm: planning
resolved_by: slot-14
locked_by:
execution_scope: orchestrator-agent
drift_direction: correct-codex
depends_on: []
last_updated: 2026-07-31
locked_since:
---

# plan-commit-sha-evidence ratchet regression — fabricated SHA 7e0aab35f

## What I found

`plan-commit-sha-evidence` (a shrinking-ratchet post-gate check in `unified-trading-pm/scripts/quality-gates.sh`)
currently reports 23 unresolvable `<repo>@<sha>` citations against a baseline of 18 — a real regression, blocking every
commit to this repo until fixed or the specific new drift is confirmed pre-existing/non-fabricated and re-baselined.

All 5 new violations cite the identical SHA `unified-trading-pm@7e0aab35f`, which does not exist anywhere in this repo's
git history (`git cat-file -e` fails; `git log --all` finds nothing matching). It appears in:

- `plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md:258`
- `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:162`
- `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:167`
- `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:170`
- `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:181`

`git log` on the breaking_change_differ doc shows the citation landed via `a1dcab5f8` ("docs(plans): flip
detect_breaking_change.py registry-data-dict blind-spot todo (unified-trading-pm@7e0aab35f,
unified-api-contracts@e34afc1d, system-integration-tests@67db4da)"). This is exactly the fabricated-evidence class
`mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` (the ratchet's own `source:`) exists to catch.

## Why it matters

The green-tree HARD RULE means this blocks EVERY commit to `unified-trading-pm` fleet-wide (verified: my own unrelated
tradfi issue-doc commit hit this via the real `quality-gates.sh --no-fix` run, not just a standalone script call). Left
unaddressed, either the fleet silently works around it (defeating the gate) or genuinely stalls PM commits.

## Recommended decision

- [x] ✅ [AGENT] P1. Investigate whether the originally-cited fabricated SHA (prefix `7e0aab35f`, this repo —
      deliberately NOT written in `repo@sha` citation shape here, so this explanatory sentence itself doesn't re-trip
      the ratchet) is a typo'd/truncated form of a REAL commit and correct the citation. — that SHA is genuinely
      fabricated (confirmed absent via `git cat-file -e` and `git log --all`); the real work landed as the single commit
      `unified-trading-pm@5607023a2` ("fix(cicd): teach detect_breaking_change.py to track registry data-dict contract
      surface"), whose diff (`/codex/08-workflows/ci-cd-flow.md` + `scripts/cicd/detect_breaking_change.py` +
      `tests/unit/test_detect_breaking_change.py`) covers design + implementation + tests + docs together — confirmed
      via `git log -- scripts/cicd/detect_breaking_change.py`. NOTE: an earlier fix attempt (commit `88126c5e1`, by the
      slot that also filed this doc) had already partially addressed this by re-citing `5607023a2` for 3 of the 5
      occurrences, but for the remaining 2 (the `[DESIGN]`-flavored citations in
      `ci_satellite_ao_dispatch_batch2_2026_07_29.md:258` and
      `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:162`) it invented a SECOND non-existent SHA
      (prefix `0b17f0747`, again this repo — same deliberate non-citation-shape note applies), claiming a separate
      "initial extend" commit that never existed — the exact same fabrication class this ratchet exists to catch.
      Corrected both remaining occurrences to cite `5607023a2` alone. `plan-commit-sha-evidence` now reports "all
      checkable citations resolve; at/below baseline" (18, matching the pre-regression baseline exactly).
- [x] ✅ [OPERATOR] P2. Moot — a real commit (`unified-trading-pm@5607023a2`) WAS located covering all the claimed work
      (design, implementation, tests, docs), so none of the 3 backing checkboxes
      (`ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s `[FIX] P1` + the `[DESIGN]`/`[FIX]`/`[TEST]` items in
      `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`) need re-verification as "claimed but never
      shipped" — the work genuinely shipped, only the citation was wrong (twice). No operator decision needed.

## Progress Log

- 2026-07-31 (slot 14): Verified `unified-trading-pm@5607023a2` is the single real commit covering the entire claimed
  PM-side scope (design/implementation/tests/docs in one diff). Found that the prior partial-fix commit `88126c5e1` had
  itself fabricated a second SHA (`0b17f0747`) for 2 of the 5 occurrences instead of citing `5607023a2` alone. Corrected
  both remaining occurrences in `ci_satellite_ao_dispatch_batch2_2026_07_29.md` and
  `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`. `plan-commit-sha-evidence` now passes at/below
  the 18 baseline (verified via `.venv/bin/python scripts/quality_gates/check_plan_commit_sha_evidence.py`). Both todos
  resolved; no re-verification needed since a real backing commit was found.

- 2026-07-31 (slot 9): Found while shipping an unrelated tradfi finding. Verified pre-existing (reproduced with my own
  diff removed + after a fresh `git pull --ff-only`), isolated the exact new violations via a diff against the baseline
  yaml, confirmed the SHA is genuinely absent from git history (not a stale-sibling-clone artifact — re-pulled all cited
  repos, still unresolvable). Filed this doc + declared a repo-blocker rather than absorbing the fix into my own
  out-of-scope task, per worker.md §4b.

## Codex SSOTs

None — this is a ratchet-baseline correction on an existing mechanism, no new contract introduced.
