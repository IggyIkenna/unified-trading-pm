---
title: "unified-trading-pm: CHANGELOG.md missing"
created: 2026-05-19
author: slot-5
resolved: 2026-05-20
resolution:
  SHIPPED — operator picked Option A (add now) 2026-05-20. CHANGELOG.md created at unified-trading-pm/CHANGELOG.md
  (PM@e8bcff952). Post-1.0.0 release-notes runbook upgrade tracked at plans/active/release_notes_runbook_post_1_0_0.md
  (stub-awaiting-1.0.0).
source:
  - "MECH14-PM-CHANGELOG-AUDIT (orchestrator task)"
locked_by: live-defi-rollout
---

> **🟢 RESOLVED 2026-05-20** — operator picked Option A (add now). CHANGELOG.md shipped at PM@e8bcff952. Post-1.0.0
> runbook upgrade has named successor `release_notes_runbook_post_1_0_0.md`. Archiving.

## What I found

`unified-trading-pm` has no `CHANGELOG.md` or `CHANGES.md`. The repo uses conventional commits + semver-agent for
version tracking — that is the machine-readable record — but there is no human-readable summary of workspace-level
changes for operators or external reviewers.

No codex doc or cursor-rule mandates a CHANGELOG for PM.

## Why it matters

- Operators onboarding to a workspace snapshot have no concise "what changed this week" reference without trawling
  `git log`.
- Auditors reviewing the workspace post-cutover (May-23 gate) will ask for a human-readable account of schema and
  pipeline changes made in May 2026.
- Downstream repo changelogs (if they exist) have no PM anchor to cross-reference against.

## Recommended decision

**Option A (recommended):** Do nothing. The workspace is pre-1.0.0; conventional commits + semver-agent provide
machine-readable history. Add a CHANGELOG only at 1.0.0 graduation as part of the release-notes runbook. Document this
decision in `codex/11-project-management/` to prevent recurring audit findings.

**Option B:** Add a lightweight `CHANGELOG.md` (keep format: `## [Unreleased]` → weekly summary blocks) and designate
slot-1 main as owner for weekly updates. Adds ~15 min/week of maintenance.

**Action items (if Option B chosen):**

- [ ] Create `CHANGELOG.md` at repo root following Keep a Changelog format **[DEFERRED-OPERATOR-DECISION]** 2026-05-19
      slot 2: conditional on Option B selection; no ack found.
- [ ] Add weekly update responsibility to `ikenna_orchestrator/LEDGER.md` slot-1 duties **[DEFERRED-OPERATOR-DECISION]**
      2026-05-19 slot 2: conditional on Option B selection; no ack found.
- [ ] Add `CHANGELOG.md` presence check to `quality-gates.sh` STEP 5.7x (codex template update required)
      **[DEFERRED-OPERATOR-DECISION]** 2026-05-19 slot 2: conditional on Option B selection; no ack found.

**Current status:** Pending operator decision (A vs B). No blocking impact on May-23 gate. Recommended = Option A (do
nothing until 1.0.0 graduation). 2026-05-19 slot 2 audit: no operator ack for Option B found in \_agent_pings.md. Items
gated on operator pick.
