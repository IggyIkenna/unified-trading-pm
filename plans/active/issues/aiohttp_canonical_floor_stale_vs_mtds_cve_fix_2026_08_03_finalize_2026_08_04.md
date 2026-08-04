---
doc_type: plan
title: aiohttp canonical-floor CVE fix — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md, reclassified
  `assigned_vm: NA -> planning` by the na-eligibility-audit infra-tranche run 2026-08-04 (retroactive-reclassification
  shape, codex ao-dispatch-batch-naming-and-conflict-check.md §1(b) — name unchanged, bolt-on finalize twin). The
  source doc's 4 remaining todos (bump the canonical aiohttp floor, regenerate the manifest, propagate fleet-wide,
  re-verify alignment) are bounded/deterministic with a fully decided fix approach — nothing left to decide, only to
  execute in the doc's own already-specified sequence. This twin verifies the source doc's own stated done-when
  (0 `check-dependency-alignment.py` issues) and checks whether it is then an archival candidate.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, dependency-alignment, aiohttp, cve]
related:
  [
    /plans/active/issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  /na-eligibility-audit infra tranche, 2026-08-04 (dispatch agt-f8d9c4) — retroactive reclassification of an
  already-owned `assigned_vm: NA` doc per the skill's Phase 2/3. Conflict-check cleared: no currently-active
  `assigned_vm: planning` doc in `parent_epic: infrastructure_master` carries an open claim on
  `workspace-constraints.toml`'s aiohttp entry specifically (`cve_affected_pinned_deps_remediation_2026_06_18.md`'s
  own aiohttp thread is a different, already-`RESOLVED 2026-07-27` gap); live-verified the canonical floor is still
  `aiohttp>=3.14.1,<4.0.0` today despite a same-day neighboring commit that raised the canonical floor for
  `cryptography` only.
context_scope:
  [
    /plans/active/issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    workspace-constraints.toml,
    canonical-dependency-manifest.json,
  ]
---

# aiohttp canonical-floor CVE fix — finalize

> **Machine-gated on `issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue this plan's todo until the parent's 4 remaining todos are
> done.

## Why the parent was reclassified (read before acting)

The parent's 4 todos are bounded and deterministic: bump `workspace-constraints.toml`'s aiohttp entry to
`aiohttp>=3.14.3,<4.0.0`, regenerate `canonical-dependency-manifest.json` from it, propagate via the existing
`scripts/workspace/propagate-canonical-versions.py` tool across the repos `check-dependency-alignment.py` flags, then
re-run that same checker fleet-wide to confirm 0 issues. The doc's own "What was actually tried" section already
ruled out the naive one-line-bump shortcut (it flips the mismatch from 1 repo onto 16) and specifies the correct
multi-step sequence, so there is no remaining design/judgment call — only execution in the stated order
(`sequential: true` was already set on the parent).

## Todos

- [ ] [SCRIPT] P3. **Verify the parent's 4 todos against its own stated "Done when", then check archival
      eligibility.** Once `issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md`'s 4 todos are `[x]`:
      (1) confirm `workspace-constraints.toml` and `canonical-dependency-manifest.json` both show
      `aiohttp>=3.14.3,<4.0.0` (read the files directly, do not trust the parent's own evidence line); (2) run
      `check-dependency-alignment.py --json` fresh and confirm it reports 0 issues fleet-wide, not just for the
      repos the parent's own 16-repo list named (a repo could have independently drifted again in the interim); (3)
      grep the parent doc's remaining `- [ ]` items — if zero remain, it is an archival candidate, so run the
      standard 6-step archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), not
      just a checkbox flip. **Done when**: the fresh alignment-check result is recorded with real evidence in this
      doc's Progress Log, and the parent is either archived or its remaining open items are named here. (repo:
      unified-trading-pm)

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — §1(b) retroactive-reclassification
  naming/pairing convention this twin follows; §3 the conflict-check protocol that cleared the parent.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual todo (1) invokes.

## Progress Log

- **2026-08-04** — Authored by the `/na-eligibility-audit` infra-tranche run (dispatch agt-f8d9c4) as the paired
  finalize twin for the parent's `NA -> planning` reclassification. No work done on the parent's own todos in this
  pass; this doc exists so the reclassified plan has the finalize coverage `plans/active/task_template.md` §4
  requires.
