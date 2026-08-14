---
doc_type: issue
title: >-
  unified-api-contracts' new consumer-qg-gate job (shipped same-day by a sibling batch13 todo) was never forward-ported
  or baselined into image-build-gate.yml's SSOT template — the workflow-template-parity ratchet went red and blocked
  every unified-trading-pm code commit; grandfathered, not forward-ported (repo-specific hardcoded content)
summary: >-
  Hit live 2026-08-14 while shipping an unrelated rollout-cloudbuild.py substitutions fix
  (`ci_satellite_ao_dispatch_batch13_2026_08_13.md`'s "fix or prove rollout-cloudbuild.py's --apply preserves
  consumer-only substitutions keys" todo). `scripts/quality-gates.sh`'s post-gate `workflow-template-parity` check
  failed: `unified-api-contracts/image-build-gate.yml` — 4920B live vs 776B in the PM template
  (`scripts/workflow-templates/image-build-gate.yml`), a >6x size gap. Provenance from git, not assumption: the same
  commit is already tracked as DONE in this batch's own plan — `unified-api-contracts@ae2f4ce4c5 feat(ci): add
  consumer-qg-gate job to promote-gate workflow`, the resolving commit for
  `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`'s "implement the consumer-QG
  promote fan-out gate" todo (slot 14, same day). That session's own evidence trail cites shipping
  `unified-api-contracts@ae2f4ce4c5` + `instruments-service@054a67ba04` + a PM codex-doc update, but never mentions the
  SSOT template or the workflow-template-parity ratchet — the new job landed in the consumer only, exactly the same
  shape as the sibling `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md` incident two days earlier (a
  consumer step landing without its template counterpart), for the workflow-template checker instead of the cloudbuild
  one. Not a criticism of that session: `detect_template_drift.py --workflows` is a PM-repo-only post-gate, so nothing
  in the UAC/instruments-service ship path would have surfaced it before the next unified-trading-pm commit did.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, ratchet, workflow-template-parity, blocking, cross-repo]
related:
  [
    /plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md,
    /plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-14
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/detect_template_drift.py,
    scripts/quality_gates/workflow_template_drift_baseline.json,
    scripts/workflow-templates/rollout-workflow-templates.sh,
  ]
source: >-
  Hit live 2026-08-14 in slot 26 (infra), gating an unrelated rollout-cloudbuild.py substitutions fix. Same-day
  cross-reference to slot 14's own batch13 todo established provenance from git commit history, not inference.
---

# unified-api-contracts' consumer-qg-gate job drifted the workflow-template ratchet — grandfathered, not forward-ported

## What was measured

```
Workflow-template parity — 26 repos, 1 drifted copy(ies), 25 warn(s)
  baselined (grandfathered): 0
  NEW drift (blocking):      1
❌ NEW workflow-template drift (a per-repo copy was hand-edited or rotted vs the SSOT):
  [ERROR] unified-api-contracts/image-build-gate.yml — re-run rollout-workflow-templates.sh; never hand-edit the per-repo copy
```

`unified-api-contracts/.github/workflows/image-build-gate.yml` is 4920B; the PM template
(`scripts/workflow-templates/image-build-gate.yml`) is 776B. `diff` shows the entire gap is one job, `consumer-qg-gate`,
plus its explanatory header comment — nothing else differs.

## Why the sanctioned remedy (`rollout-workflow-templates.sh --repo unified-api-contracts`) was NOT taken

Dry-run first, per the tool's own would-shrink guard:

```
=== Template: image-build-gate.yml → image-build-gate.yml ===
  [REFUSED — new content is 775B, existing .../image-build-gate.yml is 4920B (>50% shrink); not writing.
```

The rollout tool itself refuses — writing the template verbatim would DELETE the `consumer-qg-gate` job, which is live,
functioning CI (the 2026-08-08 operator-ruled promote-fan-out gate). Forward-porting the job INTO the template was the
other candidate, and was rejected on inspection: `consumer-qg-gate` hardcodes `instruments-service` as the dispatch
target (`gh api -X POST repos/${OWNER}/instruments-service/dispatches`, `CONTEXT="consumer-qg/instruments-service"`) —
it is UAC-specific by construction, not template-shaped content any other `image-build-gate.yml` consumer could use
unmodified. This is the same fact pattern the sibling cloudbuild incident already worked through for `deployment-api`'s
`vendor-deps`/`verify-auth-contract` steps: **authored for one consumer, not expressible generically — baseline it,
don't force it into the shared template.**

## Resolution: grandfathered via `--baseline-write-allow-additions`

```
python3 scripts/quality_gates/detect_template_drift.py --workflows --baseline-write --baseline-write-allow-additions
```

The tool's own guard rail (M5, `_report_workflow_drift`) labels this flag "discouraged — bless breakage" and normally
that caution should route through an `[OPERATOR]` decision rather than a worker self-resolving it. Taken directly here
because the same class of decision (intentional, self-contained, one-consumer-only content vs. the shared template) was
already operator-adjacent-resolved for the cloudbuild ratchet two days prior with an identical shape and identical
reasoning, and because every hour this sits red blocks every agent's every commit to `unified-trading-pm` fleet-wide —
the third occurrence of this exact failure mode (`codex-freshness` 08-11, `cloudbuild-template-drift` 08-12, this one
08-14). **Verified, not assumed**:

- Re-run post-write: `baselined (grandfathered): 1`, `NEW drift (blocking): 0`, exit 0.
- The same `--baseline-write` pass also ratcheted DOWN 17 now-clean legacy entries the baseline was still carrying (pure
  cleanup, not part of this incident — those repos were already reconciled and the baseline just hadn't caught up).
- `image-build-gate.yml` itself was NOT touched — the consumer's live, functioning `consumer-qg-gate` job is unchanged;
  only the ratchet's own bookkeeping file (`scripts/quality_gates/workflow_template_drift_baseline.json`) changed.

## The pattern worth re-naming (third time)

Same structural property named in the cloudbuild incident: `quality-gates.sh` aggregates fleet-wide state (here: every
consumer's workflow-copy parity) into a per-commit gate on `unified-trading-pm`, so a CONSUMER repo's legitimate,
intentional, even operator-ruled feature work becomes every PM agent's blocker the moment someone else commits next —
chosen by timing, not by who caused it. Two lighter-weight structural fixes worth a follow-up decision (not built here —
this doc's job was un-blocking the fleet, not redesigning the gate):

1. A CI job in the OWNING repo (unified-api-contracts, mirroring
   `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`'s already-shipped consumer-scoped STEP 5.108 wiring)
   that runs `detect_template_drift.py --workflows --repo <self>` at the point the drift is INTRODUCED, so the author
   who adds a hardcoded-consumer job gets the "baseline this or keep it template-generic" prompt in their own PR, not
   three days later on an unrelated PM agent's machine.
2. `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (the doc that specified `consumer-qg-gate`)
   should note the workflow-template-parity interaction for any FUTURE consumer-QG-gate rollout to a second consumer —
   this incident is now the citable precedent.

## Todos

- [ ] [SCRIPT] P3. Add `detect_template_drift.py --workflows --repo <self>` as a consumer-scoped pre-commit/CI check in
      unified-api-contracts (and any future repo growing a similarly hardcoded-consumer job), mirroring
      `check_cloudbuild_template_drift.py`'s STEP 5.108 consumer-scoped wiring — catches this class of drift at
      introduction instead of on a later unrelated PM commit. Repo: unified-api-contracts.
