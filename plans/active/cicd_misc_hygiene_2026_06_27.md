---
doc_type: plan
title: CI/CD misc hygiene — small independent P3 cleanups (monitors, prunes, doc-archive, dep-clone, vuln drop)
summary:
  "A grab-bag of small, independent, low-risk P3 hygiene items from the cicd tracker that don't belong to a larger lane:
  push-time pre-push ratchet on carve-out paths, the 0.24.0 staging-direct fan-out post-mortem, host stale-PR/checkout
  monitoring, review-count report-only, the lint-red-reached-SIT audit, vestigial tab-branch code prune, crons self-pull
  from a QG-v2-gated ref (design), physical archive of 7 superseded plans, the AR published-vs-required lag metric, the
  CI dep-clone manifest-pinned-tag fallback, a tier-bulk-clone helper, and dropping the aiohttp --ignore-vuln block."
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, hygiene, monitors, cleanup, deps, archive, P3]
related:
  [cicd_consolidated_remaining_2026_06_24.md, ../epics/infrastructure_master.md, ../../codex/08-workflows/ci-cd-flow.md]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on:
source:
  cicd_consolidated_remaining_2026_06_24.md (scattered P3 lines ~317, 774, 779, 808, 817, 1439, 1441, 1446, 1581, 1664,
  1666, 1700)
assigned_role: infra
drift_direction: advance-code
---

# CI/CD misc hygiene

> **Independent track — no upstream dep, parallel-startable.** Mostly different files → internally parallelizable as a
> fan-out. **Model tier: Sonnet/infra.** Each item is small + self-contained; a few are pure investigations/docs.

## Tasks

- [ ] [SCRIPT] P3. OPTIONAL faster path — a push-time pre-push ratchet/lint check on the carve-out paths (immediate
      feedback on docs/plans/.github carve-out pushes). **Gate:** a carve-out push gets the ratchet check pre-push.
- [ ] [CICD] P3. EXPLORE: why the 0.24.0 fan-out used the retired staging-direct pattern despite consumers having the
      new flow — post-mortem note. **Gate:** a written root-cause note; a guard if a real gap is found.
- [ ] [SCRIPT] P3. Host stale-PR / stale-checkout monitoring (Track D) — extend the slot Slack monitoring. **Gate:** a
      stale PR/checkout raises a slot Slack alert.
- [ ] [SCRIPT] P3. Add the `required_approving_review_count>0` flag → REPORT-ONLY (reframed): surface, don't enforce.
      **Gate:** the dashboard reports repos missing the review-count flag; no enforcement added.
- [ ] [PROCESS] P3. Audit how a lint-red commit reached SIT LDR (the QG-before-commit miss). **Gate:** a written audit +
      a guard if the gap is reproducible. (release_machinery)
- [ ] [SCRIPT] P3. Prune vestigial tab-branch code in the slot scripts (keep the identity-prefix; documented-harmless
      remnants only). **Gate:** dead tab-branch code removed; slot scripts still pass; identity-prefix retained.
- [ ] [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the bare FF-pull is safe today).
      **Gate:** a design note for the gated-ref self-pull.
- [ ] [DOCS] P3. Physical archive-move of the 7 superseded source plans. **Gate:** the 7 plans are moved to the archive
      dir; references updated; inventory regen clean.
- [ ] [SCRIPT] P3. CI dep-clone fallback — prefer the manifest-pinned tag over upstream `main` (in-flight-rename gap).
      **Gate:** dep-clone resolves the manifest-pinned tag first; the rename gap is closed.
- [ ] [SCRIPT] P3. Add a tier-bulk-clone helper for `readiness-verifier` (NICE-TO-HAVE). **Gate:** the helper
      bulk-clones a tier; readiness-verifier uses it. (release_machinery)
- [ ] [DEPS] P2. TRACKED-FOR-REMOVAL — drop the aiohttp `--ignore-vuln` block once execution-service migrates off the
      vulnerable path. **Gate:** the ignore-vuln block is removed AND pip-audit stays green (only after
      execution-service migrates — verify before dropping).

## Success criteria

- The independent P3 hygiene items are closed (or have a written note/design where they're investigations).

## Codex SSOT updates

- None expected (hygiene); update `ci-cd-flow.md` only if a guard is added.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (misc hygiene lane). Independent — parallel fan-out.
