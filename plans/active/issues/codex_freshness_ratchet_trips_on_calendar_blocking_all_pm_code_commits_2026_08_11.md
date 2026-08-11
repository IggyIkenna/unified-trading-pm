---
doc_type: issue
title:
  "Codex doc-freshness ratchet went RED on the calendar, not on a change — 2 docs hit 91d and now fail every
  unified-trading-pm quality-gates.sh run, blocking all PM code commits"
summary: >-
  Measured 2026-08-11. `check_codex_doc_freshness.py` (ratchet mode, 90d staleness limit) reports 2 NEW violations:
  `/codex/05-infrastructure/live-deployment-monitoring.md` and `/codex/05-infrastructure/strategy-vm-launcher-shape.md`,
  both `last_reviewed: 2026-05-12`, both now 91d old. Neither doc changed — they aged past the limit overnight, so the
  gate flipped RED for a clean tree. Because it is a post-gate check in `quality-gates.sh`, it fails Pass 1 for EVERY PM
  code commit (no sentinel written → `quickmerge` Pass 2 refuses), for every agent on every host, until the
  `last_reviewed` dates are honestly refreshed. Confirmed general, not specific to any pending change. NOT re-baselined:
  `--baseline-write` would hand-raise a ratchet, which CLAUDE.md bans outright.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, ratchet, codex-hygiene, blocking]
related:
  [/plans/active/ci_consolidated_closeout_2026_07_25.md, /codex/12-agent-workflow/measurement-claims-discipline.md]
created: 2026-08-11
author: claude (interactive session, slot-3)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source:
  [
    "hit live 2026-08-11 gating an unrelated pure-docs change in unified-trading-pm; the failing check named the two
    docs directly via scripts/quality_gates/check_codex_doc_freshness.py",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_codex_doc_freshness.py,
    /codex/05-infrastructure/live-deployment-monitoring.md,
    /codex/05-infrastructure/strategy-vm-launcher-shape.md,
  ]
---

# A time-triggered ratchet turns every agent's next commit red

## What was measured

```
Scanned 316 codex doc(s) across 4 cutover-critical surface(s); 2 violation(s) (staleness limit: 90d).
  - /codex/05-infrastructure/live-deployment-monitoring.md: stale (91d old; last_reviewed=2026-05-12)
  - /codex/05-infrastructure/strategy-vm-launcher-shape.md: stale (91d old; last_reviewed=2026-05-12)
❌ Regression: 2 NEW violation(s) not in the baseline snapshot
```

Both are `status: current`, neither was edited. They crossed 90d by the passage of time. The check is a post-gate step
in `quality-gates.sh`, so Pass 1 exits non-zero and no `.qg_last_passed_sha` is written — and `quickmerge` Pass 2
refuses without the sentinel. That is every PM code commit, every agent, every host, starting today.

## Why this was not simply cleared

Three exits were available and two are closed:

- **`--baseline-write`** — re-baselining accepts the 2 violations as debt. That is hand-raising a QG ratchet, which
  CLAUDE.md bans without qualification ("never raise, only lower"). Not taken.
- **Bump `last_reviewed` to today** — one line, unblocks everyone in seconds, and is a LIE unless someone actually
  re-read the docs against reality. `last_reviewed` means "a human/agent checked this doc still matches the system", and
  one of these two covers the live-capital launcher path (`launch-strategy-live-vm.sh`, Copper MPC,
  `--dry-run-live-cutover-passed`). Stamping it unread is exactly the failure
  `/codex/12-agent-workflow/measurement-claims-discipline.md` was written to stop — claiming a property that was not
  measured. Not taken.
- **Actually review both docs** — the correct fix, and real work: 208 + 126 lines covering the live/forward deployment
  event contract and both strategy VM launchers. It needs someone who can verify the claims against the current scripts
  and services. That is this issue's todo.

## Todos

- [x] [DEVOPS] P1. **Re-review `/codex/05-infrastructure/live-deployment-monitoring.md`.** ✅ Done by a peer session,
      unified-trading-pm@3895be718f. It was a REAL review, not a date stamp: it caught a genuine path drift —
      `heartbeat_daemon.py` had moved from `deployment-service/deployment_service/vm/` to
      `deployment-service/scripts/vm/`, and the doc still pointed at the old location in two places. Corrected, then
      dated `last_reviewed: 2026-08-11`.
- [x] [DEVOPS] P1. **Re-review `/codex/05-infrastructure/strategy-vm-launcher-shape.md`.** ✅ Done by the same peer
      session, unified-trading-pm@3895be718f — also substantive: the doc said "the two strategy VM launchers" when two
      MORE have since been added under `deployment-service/scripts/vm/` (`launch-strategy-backtest-grid-vm.sh`,
      `launch-strategy-test-vm.sh`). Rather than silently widening the scope it added an explicit
      `SCOPE (verified 2026-08-11)` banner stating the doc is authoritative for the two CAPITAL-BEARING launchers only
      and that neither new script touches custody or real capital — so "two" now means "the two in scope", not "the only
      two that exist". Dated `last_reviewed: 2026-08-11`. **Gate verified GREEN after both**:
      `check_codex_doc_freshness.py` → `Scanned 316 codex doc(s) … 0 violation(s)`, `✅ At-or-below baseline`. PM code
      commits are unblocked; the ratchet was never re-baselined.
- [ ] [DEVOPS] P2. **Decide whether a calendar-triggered ratchet should be able to block commits at all.** The content
      of these docs did not change; the clock moved. A staleness sweep that hard-fails Pass 1 converts a documentation
      hygiene signal into a fleet-wide commit outage on an arbitrary morning, and the only fast exits are a banned
      re-baseline or a dishonest date — which is a design that pressures agents toward the dishonest one. Options to
      weigh: WARN-only for pure-age violations while staying HARD for content-drift ones; a grace band; or a scheduled
      pre-expiry nudge (the docs were 89d stale yesterday and nothing said so). Repo: unified-trading-pm.

## Note for whoever picks this up

Both docs are `status: current` and may well be entirely accurate — 91 days is not evidence of wrongness. The work is
the reading, not a rewrite. Expect the honest outcome to be "read it, still correct, dated today" for at least one.
