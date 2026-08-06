---
doc_type: issue
title:
  aiohttp canonical floor (3.14.1) stale vs market-tick-data-service's already-shipped CVE fix (3.14.3) —
  dependency-alignment gate broken since
summary: >-
  Discovered while landing an unrelated docs(plans) commit in unified-trading-pm: `check-dependency-alignment.py` fails
  with a single `external_version_mismatch` for market-tick-data-service's aiohttp pin. Root cause:
  market-tick-data-service's pyproject.toml already carries `aiohttp>=3.14.3,<4.0.0` (a documented CVE-2026-34993/47265
  fix, same lineage as the already-archived `aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md`), but
  `workspace-constraints.toml` (the canonical SSOT) was never bumped past `>=3.14.1,<4.0.0` — so the alignment gate has
  been silently broken (blocking any PM-repo quickmerge that touches dependency-checked paths) since whenever that MTDS
  bump landed.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [dependency-alignment, aiohttp, cve, quickmerge, infrastructure]
related:
  [
    /plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    /plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md,
    /plans/archive/2026_08/issues/orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md,
  ]
created: 2026-08-03
author: unknown
priority: P2
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["discovered 2026-08-03 while landing sports_af_full_entity_completion_2026_08_03.md via quickmerge"]
drift_direction: advance-code
context_scope:
  [
    workspace-constraints.toml,
    scripts/manifest/check-dependency-alignment.py,
    scripts/manifest/generate_canonical_dependency_manifest.py,
    scripts/propagation/propagate-canonical-versions.py,
    /plans/archive/2026_08/issues/orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md,
  ]
---

## What was actually tried, and why it was reverted

Attempted the "obvious" fix in-session: bump `workspace-constraints.toml`'s aiohttp entry to `>=3.14.3,<4.0.0` (matching
MTDS) and regenerate `canonical-dependency-manifest.json`. **This made the alignment check WORSE, not better** —
`check-dependency-alignment.py` does a strict spec-string comparison, not a semver-compatibility check, so bumping the
canonical floor flipped the mismatch from 1 repo (market-tick-data-service) onto **16 repos** (unified-trading-pm,
unified-trading-library, instruments-service, alerting-service, execution-service, features-service,
fund-administration-service, market-data-processing-service, ml-service, strategy-service, trading-agent-service,
client-reporting-api, unified-trading-api, batch-live-reconciliation-service, deployment-api, deployment-service — all
still declare `>=3.14.1,<4.0.0` in their own pyproject.toml).

**Reverted both files** (`workspace-constraints.toml`, `canonical-dependency-manifest.json`) back to original — this is
NOT a one-line fix, it needs the `propagate-canonical-versions.py` step (per `workspace-constraints.toml`'s own header:
_"All repos should use these ranges; propagate via propagate-canonical-versions.py"_) to push the new floor into all 16
repos' pyproject.toml files, which is a real, multi-repo, deliberate change — not something to rush as a side-effect of
an unrelated docs commit.

## Why this is likely safe to do properly (not urgent, but should get done)

`>=3.14.1,<4.0.0` does not forbid resolving to 3.14.3+ — in practice any repo without a frozen lockfile pinning an old
version almost certainly already installs a patched aiohttp today. The real value of finishing this propagation is
closing the gap so a **future** stale/frozen lock can't silently regress below 3.14.3, and so the alignment gate stops
being permanently red for market-tick-data-service. Low urgency, low risk, straightforward mechanical fix.

## Todos

- [x] ✅ [SCRIPT] P2. Bump `workspace-constraints.toml`'s aiohttp entry to `aiohttp>=3.14.3,<4.0.0` (comment already
      exists documenting the CVE lineage — just needs the version number and a note on why 3.14.3 not 3.14.1). —
      unified-trading-pm@89c194c67
- [ ] [SCRIPT] P2. Regenerate `canonical-dependency-manifest.json` via
      `scripts/manifest/generate_canonical_dependency_manifest.py` (reads only from workspace-constraints.toml, safe).
- [ ] [SCRIPT] P2. Run `scripts/workspace/propagate-canonical-versions.py` (or the equivalent per-repo pyproject.toml
      bump) across the 16 affected repos listed above — read that script's own docs/dry-run mode first, this is a
      multi-repo change and should go through each repo's own quickmerge, not a single mega-commit.
- [ ] [SCRIPT] P3. Re-run `check-dependency-alignment.py --json` fleet-wide after the propagation lands; confirm 0
      issues.

## Sequencing note

Not blocking — the existing `>=3.14.1` floor already permits patched aiohttp versions in practice. This can be picked up
whenever infra/dependency-hygiene work is next in queue; no urgency to interrupt other in-flight work for it.

**Related, more urgent, already-tracked**: `orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md` (filed independently,
same day) covers a dead slot's unpushed `unified-trading-library` aiohttp bump to `>=3.14.3` closing 3 different, real,
currently-unpatched CVEs (2026-59881/69243/69244) — that rescue is P1 and should happen first; once it lands,
unified-trading-library resolves off this doc's 16-repo mismatch list, leaving 15.

## Progress Log

- **na-eligibility-audit 2026-08-06 (infra tranche)**: **RECLASSIFY — flipped to `assigned_vm: planning`.** All 4 todos
  [SCRIPT]-tagged, bounded, mechanical aiohttp floor propagation (bump workspace-constraints.toml to >=3.14.3, regen
  canonical manifest, propagate across 16 repos, verify alignment). No banner / no operator ruling / no revert marker.
  Conflict-check cleared: no active planning doc claims the floor bump (batch1's workspace-constraints mention is
  setuptools-specific + explicitly deferred; batch1:640 cites THIS doc as the stalled-fan-out tracker; sibling NA issue
  `orphan_cve_aiohttp_fix_slot5_unpushed` claims a different mechanism with explicit sequencing).

- **context-scout 2026-08-05**: populated context_scope (5 entries).
