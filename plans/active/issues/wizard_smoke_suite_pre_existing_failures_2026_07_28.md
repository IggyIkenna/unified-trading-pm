---
doc_type: issue
title: unified-trading-system-ui wizard smoke-suite pre-existing failures found during readiness-badge work
summary: >-
  A full tests/smoke/ Playwright run surfaced 67 pre-existing, unrelated failures while shipping the capability wizard
  readiness badge — one stale count assertion fixed inline, one genuine leg-count defect (F38) and ~65 un-triaged
  failures tracked here as follow-up.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [ui, playwright, smoke, tech-debt]
related: [/plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md]
created: 2026-07-28
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: NA
resolved_by:
locked_by:
source:
  [
    full `npx playwright test --project=chromium tests/smoke/` run during capability_wizard_gap_discovery-012,
    2026-07-28,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# unified-trading-system-ui wizard smoke-suite pre-existing failures

## What I found

While shipping the capability-wizard readiness badge (`capability_wizard_gap_discovery_2026_06_11.md` P2 item), a full
`tests/smoke/` Playwright run showed **67 failures across nearly every page** (paper-trading, sports tab, deploy
console, research pages, custody stage, etc.) — none in files this task touched. Isolated re-runs of a sample showed a
MIX of causes, not one root cause:

1. **Fixed inline (this session, low-risk, one line)**: `tests/smoke/wizard.spec.ts` "isolation mode — venues tab filter
   works" asserted a hardcoded total venue count of `195`; the live venue registry has grown to `225` since that
   assertion was written (manifest drift, not a regression). Re-pinned to `225` and reverified green in isolation —
   `unified-trading-system-ui@<see commit citing this doc>`.
2. **NOT fixed — genuine, reproducible defect, deeper than a count re-pin**: `tests/smoke/wizard.spec.ts:576` ("F38 —
   broker routing info renders in Stage J for TradFi venue (venue:cme)") hits a Playwright strict-mode violation —
   `[data-testid="broker-routing-venue:cme"]` now resolves to **2** elements (`leg-venue-group-spot_long` and
   `leg-venue-group-spot_short`), not 1. Looks like the CME archetype's leg structure grew from 1 to 2 legs since this
   test was written; the locator needs re-scoping (e.g. per-leg-group) or the assertion needs updating to expect 2 —
   needs someone who owns the leg-spec registry to confirm which is correct, not a blind locator patch.
3. **NOT triaged — the remaining ~65 failures** (any-type-sweep page-render sweep, paper-trading dashboard/ledger/
   nav-shell, sports-tab colour migration, deploy-and-subscriptions, data-status drilldown, research cross-links,
   custody stage) were seen failing in the full-suite run but NOT individually re-verified in isolation. Given the
   isolation-mode test above turned out to be a stable, reproducible defect (not a flake) when re-run alone, these are
   NOT safe to assume are flakes either — they need the same isolated-rerun triage this doc's items 1-2 got, which this
   session did not have budget for (out of scope: this session's task was the readiness badge, not a smoke-suite health
   audit).

## Why it matters

`quality-gates.sh` for this repo does not run Playwright at all (tsc/ESLint/Vitest only) — the `pw:L2 ✓` evidence tag is
a per-change manual proof, not an automated gate. That means a broad, standing smoke-suite regression like this can
persist silently across many sessions/slots without ever failing anyone's actual ship gate, since each agent typically
only runs the ONE spec relevant to their own change. This doc exists so the next session that touches the wizard (or has
spare P3 capacity) can pick up the un-triaged 65 and the F38 leg-count question with this rollup as a starting point,
instead of rediscovering it from scratch.

## Recommended decision

- [ ] [UI] P3. Triage the ~65 un-verified `tests/smoke/` failures listed in this doc's "What I found" §3 — for each,
      re-run in isolation (`npx playwright test --project=chromium tests/smoke/<file>.spec.ts -g "<name>"`); classify
      each as a genuine defect (file its own follow-up) or a shared-host contention flake (no action). Repo:
      unified-trading-system-ui.
- [ ] [UI] P3. Resolve the F38 broker-routing strict-mode violation (`tests/smoke/wizard.spec.ts:576`, `venue:cme`
      resolving to 2 leg-venue-groups instead of 1) — confirm with the leg-spec registry owner whether the CME archetype
      legitimately grew to 2 legs (then update the test to scope per-leg-group) or whether this is a genuine
      duplicate-rendering bug (then fix the component). Repo: unified-trading-system-ui.
