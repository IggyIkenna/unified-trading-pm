---
doc_type: issue
title: unified-trading-system-ui block-list-parity test failing — codex/code drift (BL-12 missing, count 11 vs 10)
summary: >-
  Discovered incidentally while verifying the CI-runner-fleet-split migration (a routine quality-gates-v2 dispatch on
  unified-trading-system-ui came back red). The failure is a genuine, pre-existing application-level test
  (__tests__/scripts/block-list-parity.test.ts) unrelated to the runner migration — confirmed the job ran on a
  GitHub-hosted runner, not the self-hosted glue fleet, so this is not an infra/runner problem.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [test-failure, codex-drift, block-list]
related: [/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md]
created: 2026-08-04
author: unknown
priority: P2
parent_epic: infrastructure_master
source: "interactive session, 2026-08-04 — discovered via an unrelated CI-runner migration verification dispatch"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/09-strategy/architecture-v2/block-list.md,
    unified-trading-system-ui/lib/architecture-v2/block-list.ts,
    unified-trading-system-ui/__tests__/scripts/block-list-parity.test.ts,
  ]
---

# unified-trading-system-ui block-list-parity test failing

## What I found

Run https://github.com/IggyIkenna/unified-trading-system-ui/actions/runs/30896404779 (dispatched purely to verify the
new CI-runner VM registration, unrelated to this content) failed with 2 real test failures, both in
`__tests__/scripts/block-list-parity.test.ts`:

- `block-list.ts ↔ codex block-list.md parity > every ### BL-N section in codex has a matching id in block-list.ts` —
  `AssertionError: Codex id "BL-12" missing from block-list.ts: expected false to be true`
- `block-list.ts ↔ codex block-list.md parity > both sources agree on total count` —
  `AssertionError: expected [...] to have a length of 11 but got 10`

287/288 test files passed, 3298/3302 individual tests passed — this is an isolated, specific parity drift, not a broad
regression. The codex `block-list.md` doc declares a `BL-12` entry that the code's `block-list.ts` doesn't have, and the
two disagree on total count (11 vs 10).

## Why this wasn't fixed here

Completely unrelated to the CI-runner-fleet-split migration this session was executing — found only because a
verification dispatch happened to run on `main` and surfaced it. Did not investigate what `BL-12` should contain
(codex-authoritative, so likely the code needs the missing entry added, but didn't confirm) or why the drift arose.

## Todos

- [ ] [UI] P2. Investigate `BL-12` in `codex/.../block-list.md` (grep for it) vs `block-list.ts` — determine whether the
      code is missing an entry that should exist (add it) or the codex doc is stale (correct the doc), then fix
      whichever is wrong so both tests pass for the right reason. Gate: `block-list-parity.test.ts` green, `pw:L2 ✓` if
      the fix touches UI-rendered content per the UI-testing-layers SSOT.

## Progress Log

- **2026-08-04**: Filed while verifying batch-4 CI-runner migration
  (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) — the migration itself is unaffected (this repo's
  quality-gates-v2 job runs on GitHub-hosted infra, not the self-hosted glue fleet).
- **context-scout 2026-08-06**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (no action) — strong git-level evidence
  (unified-trading-system-ui@3c2efb2c) suggests this is already fixed, but it is not runtime-verified (vitest not run)
  and the doc's real subject-matter owner is `ui` (asset_group mistag). Disposition (retag + verify + archive) is
  already tracked as ag_closeout_audit_cross_cutting_parked_2026_08_06.md's own todo #3, owned by the `ui` tranche —
  deferring to that rather than duplicating or archiving here.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-08-06; citation verified real
  (`plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_06.md` line ~228 still carries an open
  `[DOCS] P3` retag+verify todo naming this doc, `assigned_vm: NA` there too — the disposition owner, not a duplicate AO
  dispatch).
