---
doc_type: issue
title: evidence-backed-completion sub-rule B regressed 23->24 accidental — blocks quickmerge on unified-trading-pm
summary: >-
  `check_evidence_backed_completion.py`'s sub-rule B (runtime-green claims without an `Evidence: cloudbuild=<id>`
  citation) regressed from its baseline of 23 to 24 sometime before 2026-08-09T09:5x-ish, blocking Pass-1 QG (and
  therefore quickmerge) for every unified-trading-pm commit regardless of `--files` scope, since this is a corpus-wide
  re-scan. Confirmed pre-existing (not caused by my own staged change, which only touched
  `scripts/quality_gates/ao_dispatch_visibility_baseline.yaml`) via a fresh `origin/live-defi-rollout` rebase + re-run.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [evidence-backed-completion, ratchet-regression, ci-cd, blocking, quickmerge]
related: []
created: 2026-08-09
parent_epic: infrastructure_master
source:
  cicd-worker-slot17, discovered while shipping ao_dispatch_visibility_gate_regression_34_vs_26_2026_08_09.md's final P3
  baseline-ratchet todo
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /scripts/quality_gates/check_evidence_backed_completion.py,
    /scripts/quality_gates/evidence_backed_completion_baseline.yaml,
  ]
---

# evidence-backed-completion sub-rule B regression blocks fleet-wide shipping

## Evidence

- Baseline (`evidence_backed_completion_baseline.yaml`): `claim_without_evidence_baseline: 23`.
- Live measured (2026-08-09, fresh `origin/live-defi-rollout` pull, `check_evidence_backed_completion.py`):
  `Sub-rule B regression: 24 > baseline 23`.
- **Not caused by my own change**: my staged diff only touches
  `scripts/quality_gates/ao_dispatch_visibility_baseline.yaml` (unrelated axis); re-ran the check on a clean rebase of
  `origin/live-defi-rollout` HEAD with my diff stashed — same 24-count failure reproduced.
- **Diffed the live per-file finding counts against the baseline's per-file breakdown** (baseline lists exact
  `path:line` pairs) to isolate the delta:
  - **2 NEW claims** (not in baseline at all):
    - `plans/active/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md:122` —
      `[REVIEW] P1. DONE 2026-08-09 (slot 33, review→cicd craft)` — a doc-only re-verification todo (checked 7 deferred
      items against corpus state), not an actual Cloud Build deploy; may be a scope false-positive if the checker's
      regex fires on "DONE" + a bare commit-sha citation without distinguishing a doc-audit claim from a deploy claim.
    - `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:171` —
      `[INFRA] P0. Rebuild the IS daily-definition producer...` — cites `instruments-service@cad1d322` (a commit sha)
      plus prod scheduler-run evidence (5/5 consecutive successful days), not a `cloudbuild=<id>`; may be a genuine gap
      (the actual deploy that shipped `cad1d322` to prod should have a resolvable Cloud Build id) or another scope
      false-positive.
  - **1 claim resolved** (dropped off `monitoring_control_plane_master_2026_06_10.md`'s 5-claim set, now 4) — net delta:
    +2 new, -1 resolved = +1, matching the measured 23→24.
- Neither of the 2 new claims is something I can verify/fix within a small, clear scope: doing so correctly requires
  either (a) confirming the checker's own scope-detection is over-broad for doc-only "DONE" claims (a parser-fix
  judgment call), or (b) tracking down the actual Cloud Build id (if any) that shipped `instruments-service@cad1d322` to
  prod for the second claim — both need domain investigation I don't have context for, not a mechanical fix.

## Impact

**Blocking.** This is a corpus-wide, unconditional re-scan (like the sibling `ao_dispatch_visibility_gate_regression`
issue) — it fails Pass-1 `quality-gates.sh` for ANY unified-trading-pm commit regardless of scope, blocking every slot's
ability to ship via quickmerge to this repo until either the 2 new claims are resolved (evidence added, or confirmed
false-positive and reworded) or the baseline is reviewed-and-ratcheted (only after genuine investigation — never a blind
`--baseline-write` to silence).

## Todos

- [ ] [DEVOPS] P1. Investigate `ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md:122` — determine whether the
      checker firing on this doc-only re-verification "DONE" claim is a genuine missing-evidence gap or a scope
      false-positive (the checker treating a non-deploy completion as a runtime-green claim). If false-positive, either
      reword the claim to avoid the trigger phrase or narrow the checker's detection regex (read both sides per
      findings-triage — don't reflex-narrow the regex without confirming the todo genuinely never claimed a
      runtime/deploy outcome). Repo: unified-trading-pm.
- [ ] [DEVOPS] P1. Investigate `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:171` — determine whether
      `instruments-service@cad1d322`'s deploy to prod has a resolvable Cloud Build id (check
      `gcloud builds list --filter` around the commit's landing time, or the deploy workflow run for that sha). If
      found, add `Evidence: cloudbuild=<id>` to the todo. If the claim is actually evidenced by the cited prod
      scheduler-run success logs rather than a Cloud Build deploy (i.e., no separate build step applies), reword to
      avoid the runtime-green trigger phrase, or confirm with whoever owns the checker whether scheduler-run evidence
      should count as an accepted evidence class. Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. Once both todos above land (or are confirmed false-positive and reworded), re-run
      `check_evidence_backed_completion.py --baseline-write` to ratchet `claim_without_evidence_baseline` back down to
      the resolved count — never leave the baseline absorbing this regression once it's addressed. Repo:
      unified-trading-pm.

## Progress Log

- **cicd-worker slot 17, 2026-08-09**: filed while blocked shipping an unrelated baseline-ratchet fix
  (`ao_dispatch_visibility_gate_regression_34_vs_26_2026_08_09.md`'s final P3 todo). Diagnosed the 23→24 delta down to 2
  new claims + 1 resolved claim (see Evidence above); did not attempt to fix inline — both new claims need domain
  investigation (checker-scope judgment call / cross-repo Cloud Build history lookup) beyond a small/clear fix. Declared
  repo-blocker `qg_red` for unified-trading-pm citing this doc.
