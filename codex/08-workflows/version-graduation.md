---
doc_type: codex-ssot
title: Version Graduation (0.x.x → 1.0.0)
summary: >-
  How repos graduate 0.x.x → 1.0.0 — pre-1.0.0 `feat!` is a MINOR bump (semver-agent override, never auto-crossing to
  MAJOR); 1.0.0 is a deliberate human decision requested via `request-major-bump.yml` (or `approve-major-bump.sh`) and
  executed by `/approve` on a `major-bump-pending` GitHub issue; post-1.0.0 `feat!` = MAJOR behind an approval issue.
  SIT runs for all repos at 0.1.0+.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [version-graduation, semver, major-bump, quality-gates, sit]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/06-coding-standards/quality-gates.md]
created: 2026-03-27
authoritative_for: [version graduation 0.x.x→1.0.0 (pre-1.0.0 feat! MINOR override + 1.0.0 human-approval flow)]
referenced_by: [/codex/08-workflows/deployment-flow.md, /codex/08-workflows/version-cascade-flow.md]
owner:
last_reviewed:
code_refs: [unified-trading-pm/scripts/approve-major-bump.sh]
---

# Version Graduation (0.x.x → 1.0.0)

## Overview

All repos in the Unified Trading System start at 0.x.x. The semver-agent enforces a pre-1.0.0 override: `feat!:` on
0.x.x = MINOR bump (never MAJOR, never auto-crosses to 1.0.0).

**1.0.0 is a deliberate human decision**, not an automatic graduation.

## When to Graduate

A repo should be graduated to 1.0.0 when:

- It passes quality gates consistently (ci_status = STAGING_GREEN or SIT_VALIDATED)
- Its API surface is stable (no planned breaking changes in active plans)
- SIT deployment tests pass with the repo included (requires 0.1.0+ SIT filter)
- The repo owner/team agrees it's production-ready

## How to Graduate

### Option A: GitHub UI

1. Go to the repo → Actions → `request-major-bump` → Run workflow
2. Fill in: `proposed_version = "1.0.0"`, `reason = "Production-ready after SIT validation"`
3. A GitHub Issue is created with label `major-bump-pending`
4. Telegram sends an alert with the issue URL
5. Comment `/approve` on the issue to execute
6. The bump lands on staging → SIT validates → promotes to main

### Option B: CLI

```bash
gh workflow run request-major-bump.yml \
  --repo IggyIkenna/<repo-name> \
  -f proposed_version="1.0.0" \
  -f reason="Production-ready after SIT validation"
# Wait for Telegram alert, then approve:
# Go to the issue URL and comment: /approve
```

### Option C: Admin Script

```bash
bash unified-trading-pm/scripts/approve-major-bump.sh <repo> 1.0.0 \
  --reason "Production-ready" --admin-pat $GH_PAT
```

## Post-1.0.0 Behavior

| Commit   | Pre-1.0.0        | Post-1.0.0                   |
| -------- | ---------------- | ---------------------------- |
| `fix:`   | PATCH            | PATCH                        |
| `feat:`  | MINOR            | MINOR                        |
| `feat!:` | MINOR (override) | MAJOR (opens approval issue) |

Post-1.0.0, breaking changes require explicit `/approve` on a GitHub Issue before the version bump is dispatched. This
prevents accidental API breaks in production-stable libraries.

## SIT Filter

SIT deployment tests run for all repos at 0.1.0+ (lowered from 1.0.0+). This means:

- Pre-1.0.0 repos get full integration testing
- 1.0.0 graduation is semantic ("we declare this stable"), not a test gate
