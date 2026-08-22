---
doc_type: issue
title:
  Back-merge reconciler escalated on ldr_ci_status_sha — main-only manifest fields missing from _REPO_CI_FIELDS became
  the dam Guard 2 exists to prevent
summary: >-
  Measured 2026-08-22 while resolving escalation agt-883a53 (PR unified-trading-pm#3723, main -> live-defi-rollout
  back-merge). scripts/cicd/reconcile_manifest_backmerge.py exited 2 "GENUINE NON-CI CONFLICT" on seven repos'
  repositories.<name>.ldr_ci_status_sha. Those fields are written ONLY on main — ldr-ci-monitor.yml is
  schedule-triggered and GitHub fires schedule: exclusively from the DEFAULT branch, so the monitor checks out main,
  probes each repo's LDR ref, and pushes the manifest update to main. LDR's copies are stale snapshots that arrive
  solely via this very back-merge, so a both-sides-differ drift is main being fresher, never a real disagreement. The
  reconciler's _REPO_CI_FIELDS listed only {ci_status, coverage_pct, ci_failure_reason}, so every such drift fell
  through to the human-escalation exit — blocking main -> LDR and transitively the LDR -> main drain. Primary defect
  FIXED (unified-trading-pm@7e16a3a586). Open follow-up: the same omission class may exist for other main-only
  manifest fields that were never audited against their writers.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, back-merge, workspace-manifest, promotion, merge-conflict, escalation]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: "2026-08-22"
last_updated: 2026-08-22
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: measured while resolving escalation agt-883a53 / PR unified-trading-pm#3723 (conflict_resolver, slot 33)
drift_direction: advance-code
---

# Back-merge reconciler: unclassified main-only manifest fields

## What happened (measured, not inferred)

`scripts/cicd/reconcile_manifest_backmerge.py` is Guard 2 — it exists so a `main -> live-defi-rollout` back-merge never
stalls on CI-automation churn in `workspace-manifest.json`. On 2026-08-22 it did exactly what it exists to prevent:

```
GENUINE NON-CI CONFLICT — cannot auto-resolve; escalate to human PR:
  - repositories.{deployment-service,execution-service,features-service,strategy-service,
     unified-api-contracts,unified-trading-pm,agent-orchestrator}.ldr_ci_status_sha
```

**Root cause (confirmed by reading the writer, not by grep count):** `.github/workflows/ldr-ci-monitor.yml` is
`schedule:`-triggered. GitHub fires `schedule:` only from the DEFAULT branch, so the monitor runs on `main`, checks out
`main`, probes each repo's LDR ref, and commits `ci: update ldr_ci_status (LDR-CI-red monitor) [skip ci]` +
`git push origin HEAD` — to `main` only. `ldr_ci_status` and `ldr_ci_status_sha` are therefore main-authoritative in
exactly the sense `_REPO_CI_FIELDS` was built for; they were simply never added to it.

**Fixed** — `unified-trading-pm@7e16a3a586` adds both to `_REPO_CI_FIELDS` with two regression tests. Verified against
PR #3723's real base/ours/theirs manifests: exit 2 -> exit 0, CI fields take main, `versions[]` still semver-max
(agent-orchestrator 0.100.71/0.100.75 -> 0.100.75), 26/26 repos retained, no LDR-side edit dropped.

## Why this is worth an issue doc rather than just a commit

The failure is silent-until-it-dams: the reconciler behaves correctly for years, then one bot starts writing a NEW
main-only field and every back-merge escalates to a human at once. Nothing today asserts that the set of main-only
manifest writers matches `_REPO_CI_FIELDS` — the two drift independently.

## Open follow-ups

- [ ] [SCRIPT] P2. **Audit every other per-repo and top-level `workspace-manifest.json` field for the same
      "written only on main, not in `_REPO_CI_FIELDS`/`_TOPLEVEL_CI_FIELDS`" gap.** Unaudited per-repo candidates seen
      in the live manifest: `codebase_health`, `skipped_gates`, `bypass_audit_path`, `cascade_invalidated_by`,
      `ci_trigger_branch`, `consolidation_status`. Unaudited top-level candidates: `promotion_failures`,
      `promotion_quarantine`, `sit_cross_repo_validated_repos`, `active_feature_branch`. Method that worked here: find
      the writer workflow/script, read its trigger + checkout ref + push target — a field whose only writer runs on
      `main` is main-authoritative by construction. Do NOT classify a field as CI-authoritative without that proof.
      Provenance: escalation agt-883a53, this doc.
- [ ] [SCRIPT] P3. **Add a standing check that a main-only manifest writer cannot be introduced without classifying its
      field.** Options: a test that enumerates fields written by any `schedule:`/`push: [main]` workflow and asserts
      each is in `_REPO_CI_FIELDS`/`_TOPLEVEL_CI_FIELDS`, or a comment-contract in `ldr-ci-monitor.yml` and siblings
      pointing at the reconciler. Sizing/approach is a judgment call — hence `assigned_vm: NA`. Provenance: this doc.

## Progress Log

### 2026-08-22 — conflict_resolver slot 33, escalation agt-883a53

Classified PR #3723 via the deterministic ladder in `/agents/conflict_resolver.md`: not superseded
(`git merge-base --is-ancestor origin/main origin/live-defi-rollout` false), not drain-noise (compare showed
`ahead=40, files=2`), so a real conflict. Sole conflicting file was `workspace-manifest.json`;
`plans/audit/manifest-mutations.jsonl` union-merged per `.gitattributes`. Found and fixed the reconciler gap above,
then re-ran the canonical Guard-2 recipe (the same one `ldr-to-main-promote.yml` runs inline) to resolve the merge.
