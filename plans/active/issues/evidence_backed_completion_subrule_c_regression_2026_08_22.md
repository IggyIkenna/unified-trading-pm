---
doc_type: issue
title: evidence-backed-completion sub-rule C regression (94 > baseline 93) blocking live-defi-rollout quality-gates-v2
summary: >-
  Discovered while resolving CICD escalation agt-bc04f6 (AG-closeout-linkage wall on
  unified-trading-pm's checks slice, commit 1cbaee0). That root cause is fixed and confirmed
  green (unified-trading-pm@6d9f1ee0dd, verified via a re-triggered quality-gates-v2 run). But
  the re-run still failed — a DIFFERENT, unrelated check: `check_evidence_backed_completion.py`
  sub-rule C (prod data-mutation claims without an `Evidence:` ref) now reports 94 vs a baseline
  of 93. This is a pure count-vs-baseline ratchet (no path/line identity match — see the script's
  `rule_c_regression = len(rule_c) > baseline_c`), so a NEW `- [x]` prod-data-mutation claim
  landed somewhere in the corpus without an `Evidence: manifest-delta=|vm-log=|gcs-op=|
  state-list=` citation, added by one of the many concurrent commits that landed on
  live-defi-rollout between commit 1cbaee0 and the re-run (branch moved through several
  archival/audit/dispatch commits from other slots in that window — confirmed NOT caused by
  either file this escalation touched, both of which are closeout-doc body-text edits with no
  todo checkboxes). Out of scope for a one-shot CICD escalation to root-cause among 94 flagged
  claims across a fast-moving multi-agent corpus; filing as its own tracked issue.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, evidence-backed-completion, ratchet-regression, ldr-red]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-22"
last_updated: "2026-08-22"
author: claude-session-2026-08-22
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-22 — CICD escalation agt-bc04f6 re-verify run, unified-trading-pm quality-gates-v2"]
depends_on: []
context_scope: [/plans/active/ci_consolidated_closeout_2026_07_25.md, /codex/06-coding-standards/quality-gates.md]
---

# evidence-backed-completion sub-rule C regression blocking live-defi-rollout

## What happened

- CICD escalation `agt-bc04f6` (wall_type=`ldr_qg_failure`, repo=`unified-trading-pm`) was dispatched for
  `quality-gates-v2` red on `live-defi-rollout` at commit `1cbaee00b58fbeb6db2b0b20b28a16eb8c185ef3`
  ([run](https://github.com/IggyIkenna/unified-trading-pm/actions/runs/32564154365)).
- Root cause: `check_ag_closeout_linkage.py` found `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
  (asset_group=[ci]) with no findable path (graph or body-mention) to `ci_consolidated_closeout_2026_07_25.md` — a
  baseline-0 ratchet, 1 orphan tripped it.
- Fixed via body-text mentions in `ci_consolidated_closeout_2026_07_25.md` (Track 2) and
  `ao_consolidated_closeout_2026_08_12.md` (2 more orphans that appeared mid-session from a concurrent asset_group
  retag — `solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md` /
  `defi_compute_gcp_migration_009_repeat_wedge_parked_2026_08_08.md`), rather than editing the orphan doc's own
  `related:` list (which would have tripped `archive-safety-ratchet` on a pre-existing unrelated `related:` entry in
  that file).
- Shipped `unified-trading-pm@6d9f1ee0dd` via a direct push (quickmerge blocked on an unrelated pre-existing
  `deployment-api`/`deployment-service` dependency-alignment drift — dirty-deps carve-out per CLAUDE.md; commit is a
  docs(plans)-only PM flip, no code).
- Re-triggered `quality-gates-v2` on `live-defi-rollout`
  ([run](https://github.com/IggyIkenna/unified-trading-pm/actions/runs/32569577050)) to confirm green.
- **AG-closeout-linkage no longer appears in the failure — confirmed fixed.** But the run still failed: sub-rule C
  of `check_evidence_backed_completion.py` now reports 94 mutation-claims-without-evidence vs baseline 93.

## Why this is a separate issue, not part of agt-bc04f6

- Neither file this escalation touched (`ci_consolidated_closeout_2026_07_25.md`,
  `ao_consolidated_closeout_2026_08_12.md`) contains a `- [x]` checkbox or a data-mutation claim — both edits are
  pure body-text prose additions to existing Track/finding sections.
- The branch moved through several commits from other slots between `1cbaee0` and the re-run (archival passes,
  na-eligibility-audit batches, context-scout backfill) — any one of those could carry the new unevidenced claim.
- Sub-rule C's regression check is a raw count comparison (`len(rule_c) > baseline_c`), not a path/line diff, so
  isolating the exact new claim requires diffing the full 94-item list against the 93-item `mutation_baseline_files`
  list in `scripts/quality_gates/evidence_backed_completion_baseline.yaml` — real per-claim triage, not mechanical.

## Todos

- [ ] [SCRIPT] P1. Diff the live 94-claim list (`check_evidence_backed_completion.py --workspace-root <ws>`) against
      `mutation_baseline_files` in `scripts/quality_gates/evidence_backed_completion_baseline.yaml` (93 entries) by
      claim identity (file + surrounding text, not raw line number — line numbers shift with unrelated edits) to find
      the genuinely NEW unevidenced mutation claim.
- [ ] [PLAN] P1. Either add the missing `Evidence: manifest-delta=|vm-log=|gcs-op=|state-list=` citation to that claim
      (if the mutation is real and evidence exists), or determine it's a false-positive pattern match and fix the
      checker, or — only if the claim is genuine intentional debt — re-baseline with
      `--baseline-write` (never hand-raise the number without per-claim justification).
      Re-run `quality-gates-v2` on `live-defi-rollout` afterward to confirm full green.

## Progress Log

- 2026-08-22 (slot 13, agt-bc04f6): Filed while closing out the AG-closeout-linkage escalation. That escalation's own
  wall is resolved and verified green; this sub-rule C regression is a distinct, newer, unrelated failure surfaced by
  the same re-triggered CI run. Authoring-slot ping + escalation `/done` will note both facts.
