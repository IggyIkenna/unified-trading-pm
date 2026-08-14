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
archive_exempt: true
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [test-failure, codex-drift, block-list]
related: [/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md]
created: 2026-08-04
last_updated: "2026-08-09"
author: unknown
priority: P2
parent_epic: infrastructure_master
source: "interactive session, 2026-08-04 — discovered via an unrelated CI-runner migration verification dispatch"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by: runtime-verified 2026-08-09 (npx vitest run -> 4/4 passed, block-list.ts matches codex block-list.md)
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

- [x] ✅ [UI] P2. Investigate `BL-12` in `/codex/09-strategy/architecture-v2/block-list.md` (grep for it) vs
      `block-list.ts` — determine whether the code is missing an entry that should exist (add it) or the codex doc is
      stale (correct the doc), then fix whichever is wrong so both tests pass for the right reason. Gate:
      `block-list-parity.test.ts` green, `pw:L2 ✓` if the fix touches UI-rendered content per the UI-testing-layers
      SSOT. **DONE (staleness-recheck 2026-08-09)** — `block-list.ts` carries `BL-12` (comment: "added 2026-08-04,
      gmx_v2 venue removal") and codex `block-list.md` carries `### BL-12: DeFi perp liquidation capture — no venue`;
      both id sets (`BL-1`..`BL-10`, `BL-12`, 11 total) match exactly. Runtime-verified for real (not just git-evidence,
      per the 2026-08-06 audit's own caveat that this was git-suggestive-but-unverified):
      `npx vitest run     __tests__/scripts/block-list-parity.test.ts` in `unified-trading-system-ui` → **4/4 passed**
      live.

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
- **staleness-recheck 2026-08-09**: closed the sole todo (BL-12 investigate/fix) — runtime-verified live
  (`npx vitest run __tests__/scripts/block-list-parity.test.ts` → 4/4 passed in `unified-trading-system-ui`); both
  `block-list.ts` and codex `block-list.md` already carry matching `BL-12` entries. 0 open todos remain — **ARCHIVE
  CANDIDATE** (note: the doc's own disposition owner, `ag_closeout_audit_cross_cutting_parked_2026_08_06.md`, still
  carries an open `[DOCS] P3` retag+verify todo naming this doc — that todo's "verify" half is now satisfied by this
  recheck; archival itself is out of this recheck's scope).
- **cicd escalation agt-558c62 2026-08-09**: 0 open todos, genuinely archival-eligible, but
  `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` (1007L, already over the 1000L hard line-cap) cites
  this doc via a markdown-syntax link — archiving would hit the exact deadlock documented in
  `/plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` (a same-line link-repoint
  edit in an over-cap file has no `check_line_caps.sh` carve-out). Set `archive_exempt: true`, kept `status: open`.
  Un-set once the deadlock doc's operator decision lands and the archival can complete (same batch as the
  disposition-owner's own `[DOCS] P3` todo).
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **cross_cutting_satellite_ao_dispatch_batch13b Item N, 2026-08-14**: **STALE CITATION corrected.** The "1007L, already
  over the 1000L hard line-cap" claim above no longer holds — live-verified
  `cross_cutting_consolidated_closeout_2026_07_25.md` is 733 lines, under the 1000-line hard cap. The line-cap half of
  the archival deadlock this doc's `archive_exempt: true` cites is resolved; text-only correction per Item N's scope
  (`plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`) — did not re-verify the deadlock doc's
  other conditions or unset `archive_exempt` here (left to that doc's own operator-decision-gated resolution path).
