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
    /plans/active/issues/orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md,
  ]
created: 2026-08-03
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

- [ ] [SCRIPT] P2. Bump `workspace-constraints.toml`'s aiohttp entry to `aiohttp>=3.14.3,<4.0.0` (comment already exists
      documenting the CVE lineage — just needs the version number and a note on why 3.14.3 not 3.14.1).
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

- **na-eligibility-audit 2026-08-04** (infra tranche, dispatch agt-f8d9c4): **RECLASSIFY, conflict-cleared —
  `assigned_vm: NA -> planning`.** First verdict for this doc. All 4 todos are bounded/deterministic (bump one
  `workspace-constraints.toml` entry, regenerate the canonical manifest from it, propagate via the existing
  `propagate-canonical-versions.py` tool across the named repos, then re-verify with `check-dependency-alignment.py`)
  with a fully decided fix approach — the doc's own "What was actually tried" section already ruled out the naive
  one-line bump and specifies the correct multi-step sequence; `sequential: true` was already set. **Conflict-check
  (codex `ao-dispatch-batch-naming-and-conflict-check.md` §3) run before flipping**: (a) same `parent_epic`
  (`infrastructure_master`) active `assigned_vm: planning` docs — `cve_affected_pinned_deps_remediation_2026_06_18.md`
  (619 lines, itself mid-execution) was checked in full: its own aiohttp thread is marked `RESOLVED 2026-07-27`
  (the earlier `<3.14` vcrpy-blocked cap, a DIFFERENT and already-closed gap) and its one remaining open todo
  (`[SCRIPT] P3`, "one-by-one for the rest") doesn't name aiohttp or `workspace-constraints.toml` — no overlapping
  claim. Live-verified the actual file state rather than trusting prose: `workspace-constraints.toml:11` still reads
  `aiohttp = "aiohttp>=3.14.1,<4.0.0"` today (2026-08-04) despite that doc's own same-day Progress Log (slot-9,
  neighboring commit `unified-trading-pm@13c6d1b1f`) describing a canonical-floor raise — confirmed that raise was for
  `cryptography` only; the aiohttp mentions there are per-repo (unified-trading-pm's own pyproject) fixes, not a
  canonical-floor change, so this doc's claim on `workspace-constraints.toml`'s aiohttp entry is genuinely unclaimed.
  (b) no sibling batch/finalize doc drafted earlier in this run (first RECLASSIFY this pass). (c)
  `infra_consolidated_closeout_2026_07_25.md` Track 1 does not yet cite this doc (a discoverability gap for
  `/ag-closeout-audit`, not a conflict) and its Track 1 criterion doesn't claim this specific gap. **Soft
  cross-doc note, not a conflict**: `orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md` (different tranche,
  `parent_epic: agent_operating_framework_master`) covers a related but distinct rescue (dead-slot orphan commit) for
  ONE of the 16 repos this doc's todo 3 touches (`unified-trading-library`) — live-verified that rescue has ALREADY
  landed (`unified-trading-library@d42fe019`, 2026-08-03, confirmed ancestor of this slot's synced HEAD), so todo 3's
  fleet propagation will find that repo already correct and no-op it; zero collision risk either order. Finalize twin:
  `aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03_finalize_2026_08_04.md`.
