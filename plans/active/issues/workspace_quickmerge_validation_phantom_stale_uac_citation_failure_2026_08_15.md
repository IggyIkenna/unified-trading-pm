---
doc_type: issue
title:
  workspace-quickmerge-validation's STEP 5.97 citation check deterministically fails on unified-api-contracts
  token_wrapping.py:28/33/42 while every independently-verified fresh clone of the same ref is clean
summary: >-
  Found by a 2026-08-15 /ci-reconcile sweep. workspace-quickmerge-validation.yml (schedule 0 */6, ubuntu-latest,
  non-blocking/advisory — not one of the 3 gates that block LDR->main) failed twice in a row (00:22Z run 31853398993,
  and a manual re-trigger at 01:20Z run 31856144352) with the IDENTICAL error: "[FAIL] unified-api-contracts: 3 uncited
  contract address(es) > baseline 0. New/over-baseline site(s): unified_api_contracts/registry/token_wrapping.py:28;
  :33; :42". Independently verified THREE ways that this is not a real citation gap: (1)
  `check_defi_address_citations.py --scope unified-api-contracts` run locally against the slot-21 live-defi-rollout
  clone returns "[OK] 0 (== baseline 0)"; (2) `git log` on `origin/main` for this file shows zero commits since
  `2a8599da` (2026-06-16, the citation back-fill commit) -- the file has not changed on main in two months, so there is
  no window where main's content could have regressed; (3) a genuinely fresh `git clone --depth 1
  https://github.com/IggyIkenna/unified-api-contracts.git` done live during this investigation (HEAD 4f355bb3, a promote
  commit from minutes earlier) shows lines 28/33/42 as plain multi-line dataclass-constructor syntax with NO address on
  those exact lines -- the file is correctly cited end-to-end. The failing CI run's flagged line numbers do not
  correspond to any real historical shape of this file at those lines either (the file has been in its current
  multi-line, fully-cited form since June). Root mechanism NOT isolated: the "Clone canary repos" step (`git clone
  --depth 1 <default-branch-url>` per repo, no ref pin, no post-clone content/SHA verification, silent `|| echo Skip` on
  failure) is the most likely culprit -- either an auth/token-scoped fetch hitting a lagged git backend replica for this
  very-high-churn repo, or some other clone-time inconsistency -- but this could not be confirmed without access to the
  actual GH Actions runner's raw checkout, which is not available from this session. Not chased further per the
  effort/ambiguity findings-triage rule (ambiguous, ~30-60 min already spent, root cause needs a party who can inspect a
  live runner's exact clone state).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [ci-reconcile, quality-gates, workspace-quickmerge-validation, phantom-clone, defi-citation, coverage-gap]
related: []
created: 2026-08-15
source: ci_reconcile-sweep-2026-08-15
author: ci_reconciler
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
resolved_by:
locked_by:
locked_since:
context_scope:
  [.github/workflows/workspace-quickmerge-validation.yml, scripts/quality_gates/check_defi_address_citations.py]
drift_direction: advance-code
depends_on: []
---

# workspace-quickmerge-validation phantom stale-content citation failure

## What's confirmed

- Run 1: `31853398993` (2026-08-15T00:22Z, scheduled tick) — FAILED, STEP 5.97 flagged
  `unified_api_contracts/registry/token_wrapping.py:28,33,42`.
- Run 2: `31856144352` (2026-08-15T01:20Z, manually re-triggered by this sweep to verify) — FAILED IDENTICALLY, same
  file, same 3 line numbers, same count.
- `check_defi_address_citations.py --workspace-root .tabs/21 --scope unified-api-contracts` run locally:
  `[OK] 0 (== baseline 0)`.
- `git log --oneline origin/main -- unified_api_contracts/registry/token_wrapping.py`: top commit is `2a8599da`
  (2026-06-16, the citation back-fill). Zero commits since. Baseline yaml already ratcheted to 0 for this repo.
- A fresh `git clone --depth 1 https://github.com/IggyIkenna/unified-api-contracts.git` run live during this
  investigation (new HEAD `4f355bb3`, 2026-08-15T02:20+01:00) shows lines 28/33/42 as ordinary multi-line
  `TokenWrappingRule(...)` syntax with no bare address on those lines — fully cited, matches local state.

## What's NOT confirmed

The exact mechanism by which the CI runner's clone of `unified-api-contracts` diverges from every other
independently-verified clone of the same branch. Candidates, none confirmed:

- The "Clone canary repos" step (`workspace-quickmerge-validation.yml`) clones via
  `https://x-access-token:${GH_PAT}@github.com/...` with `--depth 1` and no ref pin, no SHA/content verification after
  clone, and silently continues past a failed clone (`|| echo "Skip $repo"`) — there is no way to tell from the run log
  whether the clone that produced the stale content actually succeeded fully or partially.
- A very-high-churn repo (unified-api-contracts promotes on a `*/15` cadence with large batches — see this session's
  other findings on promote-batch races) could plausibly hit a momentarily-lagged git backend replica on a token-authed
  fetch, though `--depth 1` HTTPS clones are normally strongly consistent and this file hasn't changed in 2 months
  regardless, which makes a REPLICA-LAG explanation weak — a lagged replica would still be lagging behind _some_ real
  historical commit, and no historical commit to this file has ever had the flagged shape at those exact line numbers.

## Why not chased further this session

`workspace-quickmerge-validation` is schedule-only and advisory — per CLAUDE.md the only three gates that actually block
LDR→main promotion are `sit-gate/fleet-green`, `quality-gates-v2`, and quickmerge-provenance. This monitor is not in
that set, so the phantom failure is not blocking anything live. Root-causing the actual clone-time divergence needs
either (a) a runner-side debug run with the clone step's stdout NOT suppressed to `/dev/null` and a `git log -1` echoed
right after each clone, or (b) reproducing it enough times to catch it live via GH Actions' own diagnostics — both are
more than the ambiguous-finding time budget for a single sweep.

## Todos

_(converted from a plain numbered "Suggested next step" list — 2026-08-19, `/plan-reconcile
agent_operating_framework_master` Phase 2 zero-checkbox sweep — no real work content changed.)_

- [ ] [INFRA] P2. Add a debug step to `workspace-quickmerge-validation.yml` (or a scratch dispatch) that, right after
      cloning `unified-api-contracts`, echoes `git -C unified-api-contracts log -1 --format='%H %ai %s'` and
      `git -C unified-api-contracts show HEAD:unified_api_contracts/registry/token_wrapping.py | sed -n '25,45p'` to
      the job log. Done when: the debug output shows definitively whether the CLONE itself got stale/wrong content,
      or whether something downstream (the checker script's own resolved workspace-root, a stray second
      `unified-api-contracts` directory, etc.) is the actual culprit.
- [ ] [INFRA] P2. BLOCKED-ON:above — if the debug step confirms a clone-time issue, harden the "Clone canary repos"
      step to verify the clone succeeded with real content (e.g. assert `.git` exists and `git rev-parse HEAD`
      succeeds) and retry once on failure/mismatch, rather than the current silent `|| echo Skip`.
- [ ] [INFRA] P2. BLOCKED-ON:above — re-run `workspace-quickmerge-validation.yml` after the fix lands and confirm 3
      consecutive green ticks before closing this doc.

## Progress Log

- 2026-08-15 (ci_reconciler, slot 21): Filed after two identical failures (scheduled + manual re-trigger), confirmed via
  3 independent methods that current content is clean, root mechanism not isolated within this sweep's time budget. No
  code changed — this doc is the tracked follow-up per findings-triage (ambiguous, not fixable this pass).
- **context-scout 2026-08-15**: populated context_scope (2 entries).
- 2026-08-15 19:07:50Z (ci_reconciler, slot 20): Independent 2026-08-15 sweep re-triggered
  `workspace-quickmerge-validation.yml` (run `31903044862`) to test whether an unrelated fix (the same run's
  `ModuleNotFoundError: No module named 'pydantic'` retry-storm) was masking this as a transient flake — it recurred
  IDENTICALLY (same 3 lines, same count), a third occurrence with the same signature. Independently re-confirmed local
  `main` branch content via `gh api repos/IggyIkenna/unified-api-contracts/contents/...?ref=main` is correctly cited at
  lines 28/30/33 (not 28/33/42 — the flagged line numbers don't even match the real file's address positions), and
  `_line_is_uncited()`'s same-line `comment_idx`/`DERIVED_MARKER` logic in `check_defi_address_citations.py` is correct
  for this content shape. Did not re-chase the clone-time mechanism beyond this — same effort/ambiguity call as
  slot-21's original triage still holds. No code changed by this entry.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:b10d22b59c109ec8]: KEEP-NA, valid — genuine unresolved phantom-CI investigation needing GH Actions runner-side debug access not available to this session; correctly not escalated further since the failing workflow is schedule-only/advisory.
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (2 entries), unchanged.
- **context-scout 2026-08-20**: refreshed context_scope (2 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — all 3 remaining `[INFRA] P2` todos
  form a sequential BLOCKED-ON chain needing GH Actions runner-side debug access not available to this session,
  against a workflow that is schedule-only/advisory (not one of the 3 gates that block LDR→main) — correctly
  deprioritized, re-affirming the 2026-08-17 verdict.
