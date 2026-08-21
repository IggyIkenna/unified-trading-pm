---
doc_type: issue
title: deployment-service — pre-existing full-sweep QG failures (fallback-import baseline overage, hardcoded prod project ID in tests)
summary: >-
  While independently verifying a Phase 2 relocation sub-agent's `bash deployment-service/scripts/quality-gates.sh
  --no-fix` run (migration_script_canonicalization_into_deployment_service_2026_08_18.md), the FULL gate sweep
  failed on two checks unrelated to the sub-agent's own change: (1) STEP 5.94 fallback-import baseline overage at
  `scripts/sync/sync-configs.py:267`, and (2) a hardcoded-prod-project-id check flagging `central-element-323112`
  literals spread across many lines in `tests/unit/test_data_pipeline_monitors.py` and
  `tests/unit/test_consolidator_watchdog_vm_wiring.py`. Confirmed pre-existing and unrelated to the migration plan's
  work: `git log -1 -- scripts/sync/sync-configs.py` shows it was last touched 2026-07-09 (weeks before this
  session), `git diff HEAD` on all three files is empty (byte-identical to the committed tree), and the hardcoded
  project-ID literals appear on many separate lines across both test files, consistent with long-standing test
  fixture code rather than a new regression. Not fixed here -- root cause needs investigation (is the
  fallback-import baseline threshold itself flapping/non-deterministic, or did a genuine new violation land
  elsewhere in the corpus and get attributed to this file's line count; is the hardcoded project ID acceptable in
  test fixtures or does it need a shared constant) -- both are judgment calls, not mechanical fixes, and are
  entirely outside the migration-script-canonicalization plan's scope. Notable: `quickmerge.sh`'s own pre-commit
  checks do NOT run the full sweep, so several unrelated commits landed on `live-defi-rollout` successfully this
  session despite this latent full-sweep failure -- worth knowing before assuming a green quickmerge means a green
  full `quality-gates.sh` run.
status: open
nature: issue
asset_group: [infrastructure] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; generic QG/test-hygiene findings (fallback-import baseline, hardcoded project ID in tests), not data-pipeline scope
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [quality-gates, baseline-ratchet, hardcoded-config, test-hygiene]
related:
  [
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
# was: infrastructure_master (renamed 2026-08-18, epic-taxonomy restructure; corrected cross-epic sweep 2026-08-19)
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: engineer
effort: low
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
    deployment-service/scripts/sync/,
    deployment-service/tests/unit/,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-19 while independently re-verifying a Phase 2 relocation sub-agent's full quality-gates.sh
    run (deployment-service) as trust-but-verify -- the sweep failed on 2 checks unrelated to the sub-agent's own
    change. Item 1 escalated from a low-priority finding to a real blocker mid-session when it began rejecting
    this orchestrating session's own quickmerge commits.",
  ]
locked_by:
locked_since:
---

## What I found

Independently re-running `bash deployment-service/scripts/quality-gates.sh --no-fix` (as part of trust-but-verify
on a Phase 2 relocation sub-agent's self-report) surfaced two failures with zero relationship to the change being
verified:

1. **STEP 5.94 fallback-import baseline overage** — `scripts/sync/sync-configs.py:267`. This is a ratchet check
   (baselines should only shrink, never grow) per `/codex/06-coding-standards/quality-gates.md`. The file itself
   has not changed (`git log -1` → `3262d7c1 2026-07-09`), so either the baseline threshold itself moved (a
   config/baseline-file change elsewhere), or the check's corpus-wide count shifted from unrelated fleet activity
   and this file's line just happened to be the one reported as over.
2. **Hardcoded prod project ID** (`central-element-323112`) in `tests/unit/test_data_pipeline_monitors.py` and
   `tests/unit/test_consolidator_watchdog_vm_wiring.py` — many separate line hits in each file (not a single
   isolated literal), consistent with long-standing test-fixture code, not a new regression.

Both files are byte-identical to `HEAD` (`git diff HEAD -- <path>` empty) — confirmed via direct `git log`/`git
diff`, not just trusting the sub-agent's own claim.

## Why this matters

This is a currently-failing full `quality-gates.sh` sweep sitting on `live-defi-rollout`'s HEAD for
deployment-service. It did NOT block this session's several successful `quickmerge.sh` ships to deployment-service
(quickmerge's own pre-commit hooks are a narrower check set than the full sweep) — but any future session that
runs the FULL sweep and expects green-before-commit per this workspace's HARD RULE will hit this and may
mis-attribute it to their own change if they don't check `git diff HEAD` first, the way this investigation did.

## Update 2026-08-19 — item 1 RESOLVED, became a real blocker mid-session

This stopped being a low-priority "unrelated pre-existing" finding once it started FAILING quickmerge's own
commit-time re-gate step for deployment-service — two separate quickmerge attempts shipping unrelated Phase 2
migration-plan work were rejected with "Sentinel NOT written" on this exact STEP 5.94 check, blocking all further
deployment-service commits fleet-wide (not just this plan's work). Root-caused: `scripts/sync/sync-configs.py:267`
wrapped a plain `from unified_trading_library import (...)` inside a `try: ... except (ImportError, OSError,
ValueError, RuntimeError):` block — a legitimate function-scoped lazy import, but the `ImportError` in the except
tuple made the checker count it as a fallback-import shim, pushing the file's site count to 3 against a baseline
of 2. Fixed by separating the import (now unconditional, outside any try/except) from the client-construction
error handling (kept, now only catching `(OSError, ValueError, RuntimeError)` for the actual construction calls) —
`unified_trading_library` is deployment-service's own core direct dependency, not optional, so no `# noqa:
fallback-import` was warranted. Re-ran `check_no_fallback_imports.py --scope deployment-service` →
`[OK] deployment-service: 2 (== baseline)`. Full `quality-gates.sh --no-fix` green. Shipped
`deployment-service@7269d436f2` (bundled with the Phase 2 relocation batch it was blocking).

**Item 2 (hardcoded `central-element-323112` in `tests/unit/test_data_pipeline_monitors.py` /
`test_consolidator_watchdog_vm_wiring.py`) is still open** — did not block shipping (it's a different, apparently
non-hard-failing check in the sweep, or was masked by the item-1 failure aborting the run first each time), and
fixing it properly is still a judgment call (whether the hardcoded ID is acceptable in test fixtures or needs a
shared constant) outside the migration-canonicalization plan's scope. Needs its own pass.

## Todos

- [ ] [ENG] P2. **Resolve the hardcoded `central-element-323112` prod project ID** in
      `deployment-service/tests/unit/test_data_pipeline_monitors.py` and
      `deployment-service/tests/unit/test_consolidator_watchdog_vm_wiring.py` (many separate line hits in each file).
      Judgment call: decide whether a hardcoded prod project ID is acceptable in test fixtures as-is, or needs a
      shared constant/fixture. Done when: the QG hardcoded-project-id check passes clean for both files, or an
      explicit exemption is recorded with rationale.

## Progress Log

- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 0 open checkboxes (grep-verified, matches Phase-0=0) — the doc uses pure prose, no checkbox syntax at all. Item 1 (fallback-import baseline overage) is fully resolved and shipped.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **ag-closeout-audit 2026-08-21 (infra tranche hygiene fix)**: converted item 2's prose-only "still open" claim into
  a real `- [ ] [ENG] P2` checkbox — the doc previously carried zero checkbox syntax despite describing genuine open
  work, a HARD RULE violation (every deferral must be a tracked `- [ ]`, not prose).
