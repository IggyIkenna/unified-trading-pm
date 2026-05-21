---
title: Release-notes runbook — post-1.0.0 graduation
parent_epic: infrastructure_master
priority: P3
status: paused
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
locked_by: live-defi-rollout
locked_since: 2026-05-12
related_plans: []
---

# Release-Notes Runbook — Post-1.0.0 Graduation

> **Status**: STUB. This plan activates when the workspace approaches version 1.0.0 graduation (post-cutover,
> post-stability). Until then, the lightweight `CHANGELOG.md` at unified-trading-pm root is the canonical changelog
> surface.

Runbook owner: ikenna · Cadence: at-1.0.0-graduation · Verifier: ikenna · Last executed: stub (not yet executed)

---

## Scope (when activated)

- [ ] [SCRIPT] P3. Auto-generate per-version sections from conventional-commit history (// prefixes already in use).
- [ ] [SCRIPT] P3. Per-service release notes (separate from workspace-level changelog).
- [ ] [AGENT] P3. Operator-facing summary (one-paragraph per version) + agent-facing diff (full commit list).
- [ ] [SCRIPT] P3. Wire into semver-agent's bump workflow so version bumps auto-add a section.

## Trigger condition

Moves from to when: a repo bumps to 1.0.0 (via ), OR operator declares stability gate reached (DeFi + CeFi + TradFi all
running clean ≥30 days).

## Temporary states + canonical follow-up plans

- Pre-1.0.0: lightweight CHANGELOG.md only (per ikenna 2026-05-20). No deferral — explicitly paused pending graduation
  trigger.
