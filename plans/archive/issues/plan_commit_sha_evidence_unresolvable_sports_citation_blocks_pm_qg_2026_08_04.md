---
doc_type: issue
title: plan-commit-sha-evidence ratchet regression (23 > baseline 22) blocks unified-trading-pm QG
summary:
  "scripts/quality_gates/check_plan_commit_sha_evidence.py's ratchet check fails corpus-wide (23 unresolvable
  resolved_by:/<repo>@<sha> citations found vs baseline 22 in plan_commit_sha_evidence_baseline.yaml) due to ONE
  citation not in the recorded baseline set: plans/archive/2026_08/sports_satellite_ao_dispatch_batch2_2026_07_24.md:769
  cites `unified-trading-pm@9022488a2` (PR #1492), and that SHA does not resolve anywhere in this repo's local git
  history (`git cat-file -e`, `git rev-list --all | grep`, both empty). This blocks `bash scripts/quality-gates.sh` (and
  therefore quickmerge Pass-1) for EVERY slot shipping any unrelated unified-trading-pm change, confirmed pre-existing
  on my own unrelated task (fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md) — the citation's
  own doc dates the entry 2026-07-25, well before this session, and my diff never touched that file."
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [qg-red, plan-hygiene, commit-sha-evidence, repo-blocker, ratchet]
related:
  [
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-08-04
author: slot-8
parent_epic: plan_hygiene_master
priority: P2
source:
  [
    "2026-08-04 (slot-8) — discovered while shipping an unrelated fix
    (fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md): `bash scripts/quality-gates.sh` failed
    the plan-commit-sha-evidence ratchet check (23 > baseline 22). Confirmed the extra citation predates this session
    and my diff never touches the offending file.",
  ]
assigned_vm: planning
resolved_by: unified-trading-pm@64c4bfdab
locked_by:
execution_scope: orchestrator-agent
drift_direction: investigate
depends_on: []
last_updated: 2026-08-04
context_scope:
  [
    scripts/quality_gates/check_plan_commit_sha_evidence.py,
    scripts/quality_gates/plan_commit_sha_evidence_baseline.yaml,
    plans/archive/2026_08/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# plan-commit-sha-evidence ratchet regression blocks unified-trading-pm QG

## What I found

`scripts/quality_gates/check_plan_commit_sha_evidence.py` scans every `resolved_by:`/`<repo>@<sha>` citation in
`plans/archive/2026_08/**/*.md` and fails if the count of citations that don't resolve to a real commit in the cited
repo's local clone exceeds the recorded baseline (`scripts/quality_gates/plan_commit_sha_evidence_baseline.yaml`,
currently 22). A full `bash scripts/quality-gates.sh` run on 2026-08-04 (slot-8) found 23:

```
Unresolvable commit-SHA citations: 23 (baseline 22).
```

Diffing the live output against the 22 baseline entries (matching by `<repo>@<sha>` string; line numbers drift as
unrelated docs above them grow), every baseline entry is still present — the ONE new entry is:

```
plans/archive/2026_08/sports_satellite_ao_dispatch_batch2_2026_07_24.md:769: [todo] unified-trading-pm@9022488a2
```

Context (line 769 of that file): `...issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`
`(unified-trading-pm@9022488a2, PR #1492)`. Checked whether this is a shallow-clone/not-yet-fetched issue rather than a
genuine bad citation: `git cat-file -e 9022488a2` → `fatal: Not a valid object name`;
`git rev-list --all | grep '^902248'` → empty (no match anywhere in local history, including all
branches/reflog-reachable commits). The cited repo is `unified-trading-pm` itself (not a sibling clone that might be
absent), so this isn't the sibling-clone-missing case the checker already tolerates — the SHA is either
mistyped/fabricated or belongs to a commit that has since been rewritten out of history (e.g. a squash/rebase on a
since-superseded branch).

**Confirmed pre-existing, not caused by my session's work**: my own task's diff
(`scripts/plan-hygiene/fix_frontmatter.py` + `tests/unit/test_fix_frontmatter_issue_author_field.py`) never touches
`plans/archive/2026_08/sports_satellite_ao_dispatch_batch2_2026_07_24.md`, and that doc's entry is dated
`2026-07-25T08:34Z (slot 7, data_engineering)` in its own body — 10 days before this session and 5 days before the
2026-07-30 baseline file was authored. It's unclear why the baseline capture on 2026-07-30 missed this citation
(possibly authored/edited after that baseline run, or a transient scan gap) — not investigated further here since
root-causing the baseline-authoring gap itself is out of scope for unblocking today's ship.

## Why it matters

- Blocks `bash scripts/quality-gates.sh` — and therefore quickmerge Pass-1 — for EVERY slot shipping ANY unrelated
  `unified-trading-pm` change, not just work that touches the offending doc. This is a corpus-wide ratchet gate, so one
  bad citation anywhere in `plans/archive/2026_08/` blocks the whole fleet.
- If the SHA is genuinely fabricated (not just a rewritten/rebased commit), it's exactly the class of violation
  `check_plan_commit_sha_evidence.py` was built to catch per CLAUDE.md's "Runtime verification" hard rule
  (`plans/archive/2026_08/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`) — a `- [x]` claim citing
  proof that doesn't actually exist. It should not be silently re-baselined away without confirming which case this is.

## Recommended decision

A human/worker with `unified-trading-pm@main` GitHub access should resolve PR #1492 via `gh pr view 1492` to find the
actual merge/squash SHA, then either: (a) correct the citation in
`sports_satellite_ao_dispatch_batch2_2026_07_24.md:769` to the real resolvable SHA, or (b) if PR #1492 genuinely doesn't
exist / was never merged, flag the citation as unverifiable in the doc itself (don't silently delete evidence of a real
finding — the underlying claim, the api_football per-fixture hard-failure fix, may still be true; only the SHA citation
is suspect).

Only after (a) or (b) should `scripts/quality_gates/plan_commit_sha_evidence_baseline.yaml` be re-verified against the
corrected corpus (baseline should return to 22, or drop further if the citation is fixed rather than just annotated —
never `--baseline-write`d up to 23 to paper over an unconfirmed-fabricated citation).

## Todos

- [x] ✅ [SCRIPT] P2. Resolve PR #1492 via `gh pr view 1492 --repo IggyIkenna/unified-trading-pm` (or equivalent) to
      find the real merge SHA for the `api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`
      finding cited at `plans/archive/2026_08/sports_satellite_ao_dispatch_batch2_2026_07_24.md:769`. Correct the bad
      citation (repo `unified-trading-pm`, cited SHA `9022488a2` — note the space, not `@`, to avoid this todo itself
      matching the very citation regex it's about) to the real resolvable SHA, or annotate it unverifiable if PR #1492
      doesn't exist. Re-run
      `python3 scripts/quality_gates/check_plan_commit_sha_evidence.py --workspace-root $WORKSPACE_ROOT` to confirm the
      corpus is back to 22 unresolvable citations (the pre-existing baseline, not a re-baselined 23). (repo:
      unified-trading-pm)

## Progress Log

- 2026-08-04 (slot-8): filed after `bash scripts/quality-gates.sh` blocked shipping an unrelated fix
  (`fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md`) on this pre-existing corpus regression.
- 2026-08-04 (slot-8) RESOLVED: `gh pr view 1492 --repo IggyIkenna/unified-trading-pm` returned the real merge commit
  `ac4ace8b9e38de6b9294009ace107dc9af80aaf8` (merged 2026-07-25T08:48:11Z) — confirmed it resolves locally
  (`git cat-file -t` → `commit`) and its message/date match the cited finding. The original `9022488a2` was a genuine
  bad citation (mistyped or fabricated), not a rewritten-history case. Corrected
  `sports_satellite_ao_dispatch_batch2_2026_07_24.md:769` to cite the real SHA (short form `ac4ace8b9`) with an inline
  note on the correction. Re-ran `check_plan_commit_sha_evidence.py` — corpus is back to 22/22, at baseline (no
  re-baseline needed). No repo-blocker was declared in the end since the fix landed within the same turn.
