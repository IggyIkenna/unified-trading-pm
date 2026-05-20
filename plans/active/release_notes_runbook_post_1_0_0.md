---
name: release_notes_runbook_post_1_0_0
status: stub-awaiting-1.0.0
priority: P3
parent_epic: governance
related_plans:
  - changelog seed at CHANGELOG.md (added 2026-05-20)
execution:
  owner: ikenna
  cadence: at-1.0.0-graduation
  verifier: ikenna
  last_executed: stub (not yet executed — activates at 1.0.0 graduation)
---

# Release-notes runbook — post-1.0.0 graduation

> **Status**: STUB. This plan activates when the workspace approaches version 1.0.0 graduation (post-cutover,
> post-stability). Until then, the lightweight `CHANGELOG.md` at unified-trading-pm root is the canonical changelog
> surface.

## Scope (when activated)

- Auto-generate per-version sections from conventional-commit history (the `feat:`/`fix:`/`docs:` prefixes already in
  use).
- Per-service release notes (separate from this workspace-level changelog).
- Operator-facing summary (one-paragraph per version) + agent-facing diff (full commit list).
- Wire into the semver-agent's bump workflow so version bumps auto-add a section.

## Trigger condition

This plan moves from `stub-awaiting-1.0.0` to `in-flight` when:

- A repo in the workspace bumps to 1.0.0 (per `request-major-bump.yml` workflow), OR
- Operator declares stability gate reached (DeFi + CeFi + TradFi all running clean for ≥30 days).

## Why deferred

Pre-1.0.0 the toil-vs-value ratio favours the lightweight CHANGELOG.md only. Per ikenna 2026-05-20.
