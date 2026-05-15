---
title: UTL semver bump label mismatches — fix: commits adding/removing public exports
created: 2026-05-15
author: slot-8
source:
  - unified-trading-library/__init__.py git log
  - .github/workflows/semver-agent.yml
locked_by: ~
---

## What I found

Audit of UTL commit labels vs actual `__init__.py` surface changes (since baseline `93e3ace`).

**Pattern: `fix:` commits added new public exports** (should be `feat:`):

| SHA | Label | What changed in `__init__.py` | Should be |
|-----|-------|-------------------------------|-----------|
| `67c532b` | `fix(utl)` | Added EmissionDecision + publish_with_policy + 4 related | `feat:` |
| `2f92d6c` | `fix(sse)` | Re-exported SSEHeartbeat + SSEMessage | `feat:` |
| `226f637` | `fix` | Added generate_download_url + generate_upload_url | `feat:` |
| `18bd238` | `fix` | Added UnifiedCloudServicesConfig | `feat:` |
| `35ad876` | `fix(core)` | Modified health_router import path (behaviour change) | borderline |

**Breaking change mislabeled as fix:**

| SHA | Label | What changed | Should be |
|-----|-------|--------------|-----------|
| `317fe6a` | `fix` | REMOVED CloudTarget + StandardizedDomainCloudService | `feat!:` |

## Why it matters

Pre-1.0.0 semver rules for this workspace:
- `feat!:` / `feat:` → MINOR bump (0.3.x → 0.3.x+1 in patch, or MINOR increment)
- `fix:` → PATCH bump

The mislabeled commits caused PATCH bumps when MINOR bumps should have fired. The `317fe6a` removal should have triggered `feat!:` (MINOR pre-1.0.0) but only fired PATCH.

**Current next-bump status**: correct. The latest batch of commits (since last CYCLE-CLOSE) all use `feat:` for export additions. Next staging bump will compute MINOR correctly.

## Recommended decision

1. **QG STEP proposal** (new enforcement): Add a STEP to `base-library.sh` that detects `fix:` commits touching `__init__.py` exports and warns/blocks. Pattern: `git log --oneline HEAD~1..HEAD | grep "^[a-f0-9]* fix" | xargs -I{} git show {} -- unified_trading_library/__init__.py | grep "^+from\|^+\"" | grep -v "^+++"` — if non-empty, emit warning.

2. **CLAUDE.md addition**: Document the rule: "Adding to `__init__.py` public exports = `feat:`; removing = `feat!:`; internal-only = `fix:` ok."

3. **Historical mismatches**: Cannot be retroactively relabeled. Document in this issue; no action needed on shipped versions.

**Priority**: P2 — next-bump is correct today; rule gap will re-surface on next export-wiring commit.
