---
doc_type: issue
title:
  check_archive_candidates.sh --only precommit mode has no exemption for the standard flip-then-mv two-commit archival
  pattern
summary: >-
  check_archive_candidates.sh's new --only precommit mode (added 2026-08-09, no baseline/ratchet by design) requires a
  doc that reaches 0 open todos + some done + unlocked to ALSO be git-mv'd to plans/archive/ in that exact same commit —
  but the plan-completion-and-archival-discipline SSOT (and the pre-existing corpus precedent, e.g.
  sports_arb_operator_group_and_commission_bugfix_2026_08_08_finalize.md's own two-commit history) mandates the
  OPPOSITE: never combine the checkbox flip with the git-mv archival in one commit, because that combination makes the
  diff at the original plan_ref path show only a file deletion, defeating the AO server's cross-repo M3 checkbox-flip
  verification. The two rules are in direct conflict for any doc whose OWN last todo is its archival trigger. Hit live
  2026-08-09 while archiving sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md; worked around with a
  temporary `archive_exempt: true` (removed in the follow-up archival commit), but the underlying gap in the check
  script is unfixed and will keep blocking every future single-todo-completing archival commit under this pattern.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, archival, precommit, tooling-gap, check_archive_candidates]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md,
  ]
created: 2026-08-09
author: data_engineering (slot 15)
parent_epic: infrastructure_master
source: ["discovered live while executing sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md todo 6"]
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
---

# check_archive_candidates.sh --only mode conflicts with the flip-then-mv archival rule

## What I found

`scripts/plan-hygiene/check_archive_candidates.sh`'s `--only` precommit-scoped mode (added 2026-08-09, per its own
header comment) flags ANY staged `plans/active/*.md` doc with 0 open todos + ≥1 done todo + no `locked_by` + not
`archive_exempt: true` — with no baseline/ratchet tolerance, unconditionally, regardless of whether THIS commit is what
brought it to 0 open todos. That forces the checkbox-flip commit and the `git mv` archival commit into ONE commit for
any doc whose own last todo is its archival trigger.

But `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (and `unified-trading-pm/agents/RULES.md` § 2)
mandates the opposite: a single commit that both flips the checkbox AND `git mv`s the file makes the diff AT THE
ORIGINAL `plan_ref` PATH show only a file deletion — no `[ ] → [x]` transition visible there for a path-scoped
`git show`/`git log` query — which defeats the AO server's `/done` M3 cross-repo checkbox-flip verification
(`cross_repo_pm_file_touched_no_checkbox_flip`). The corpus's own pre-existing precedent confirms the two-commit shape
is the norm:
`git log --oneline -- plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08_finalize.md`
shows the flip (`184945313f`) and the archival move (`9a664a1557`) as two separate, consecutive commits — but that
precedent predates 2026-08-09, i.e. before `--only` mode existed, which is exactly why it never hit this conflict.

## Why it matters

Every future doc whose own last todo is "archive this doc" will hit this exact deadlock: the flip-only commit gets
rejected by `check_archive_candidates.sh --only` demanding an immediate `git mv`, but doing that violates the
archival-discipline SSOT's checkbox-flip-vs-mv separation rule. Worked around live (2026-08-09,
`sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md`) with a temporary `archive_exempt: true` on the
flip-only commit, removed in the immediately-following archival commit — legitimate per the script's own documented
shape-(b) rationale ("a doc explicitly routed for archival... as part of a larger sequenced pass"), but this is a
workaround, not a fix, and requires every future agent to independently rediscover it.

## Recommended decision

Add a genuine exemption to `check_archive_candidates.sh`'s `--only` mode for this exact shape: a staged doc whose ONLY
diff in this commit is a todo-checkbox transition (no other line changes, or specifically no `git mv`/rename event in
this same commit) should not be flagged — the git-mv-archival commit that must follow within the same session is exactly
what the OLDER corpus-wide baseline mode already tolerates (it just re-scans on the next commit and finds the doc
archived by then). Alternative: formally document `archive_exempt: true` as the SANCTIONED bridge for this specific
two-commit pattern (update the script's own header comment + the archival-discipline SSOT to name it explicitly), so
future agents don't have to re-derive the same workaround independently.

- [ ] [SCRIPT] P2. Add an exemption to `scripts/plan-hygiene/check_archive_candidates.sh`'s `--only` mode for a doc
      whose staged diff is a pure checkbox-transition edit (no rename, no `git mv`) — OR update the script's own header
      comment plus `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` to formally document
      `archive_exempt: true` as the sanctioned temporary bridge between the flip commit and the immediately-following
      archival commit. Add a regression test covering the flip-then-mv two-commit sequence. (repo: unified-trading-pm)
