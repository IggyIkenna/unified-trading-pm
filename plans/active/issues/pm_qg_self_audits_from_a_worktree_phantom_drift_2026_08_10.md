---
doc_type: issue
title:
  PM's quality gate self-audits when run from a worktree, emitting phantom codex-SSOT drift and a baseline-corrupting
  remedy
summary: >-
  check_repo_docs_ssot excludes the PM repo by DIRECTORY NAME, so a checkout under any other name (every git worktree,
  incl. those safe-doc-push and quickmerge --isolated create) audits its own docs as a sibling repo. Measured
  2026-08-10: 14 phantom drift docs plus a printed --update-baseline remedy that would have poisoned the shared ratchet.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, worktrees, false-positive, ratchet-safety]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/06-coding-standards/quality-gates.md]
created: 2026-08-10
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: none
source: Hit live while gating the tool-call-batching hook from an isolated worktree, 2026-08-10.
depends_on: []
last_updated: 2026-08-20
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    scripts/quality_gates/check_repo_docs_ssot.py,
    scripts/dev/safe-doc-push.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
effort: low
---

# PM's QG self-audits from a worktree

## Symptom

Running `bash scripts/quality-gates.sh` from a PM **git worktree** fails with:

```
❌ check_repo_docs_ssot: 14 repo doc(s) with NEW codex-SSOT drift:
  pm-wt-hook-200727/README.md:
    - line 119: mirror-ref -> 'unified-trading-codex/' (NEW — not in repo_docs_ssot_baseline.yaml)
  ...
    python3 scripts/quality_gates/check_repo_docs_ssot.py --update-baseline
```

plus `Repo-docs-defer-to-codex drift` from the same scan. None of it is real.

## Root cause

`_iter_repo_docs()` walks every directory in the workspace root and skips PM via `repo_dir.name in _EXCLUDED_REPOS`,
where `_EXCLUDED_REPOS = {"unified-trading-pm"}`. That is a **string match on the directory name**.
`git worktree add <path>` names the directory whatever the caller passes, so from `…/pm-wt-hook-200727/` PM no longer
matches its own exclusion and audits its own `README.md` + `docs/**` as though they belonged to a sibling service repo —
where referencing `unified-trading-codex/` or a hardcoded project id IS a real violation.

This is not an exotic setup. **Worktrees are the sanctioned pattern**: `safe-doc-push.sh` is always-on isolated, and
`quickmerge --isolated` is laptop-default-ON (see `/codex/05-infrastructure/per-tab-worktrees.md`). Any agent that gates
from one hits this.

## Why it is worse than a noisy failure

The printed remedy is `--update-baseline`. Following it writes 14 phantom entries into the **shared, committed**
`repo_docs_ssot_baseline.yaml`, permanently blinding a ratchet that exists to catch real drift. A false failure that
ships a plausible, destructive fix is more dangerous than one that just fails.

## Diagnosis trap (this is the part that costs the time)

With TWO PM worktrees side by side in one scratch dir, the first run reported **28** docs — because the workspace root
resolved to the scratch dir and the sibling worktree was scanned too. Removing the sibling dropped it to **14**, which
reads like partial progress and supports the wrong theory ("it scans siblings"). It does scan siblings, but that is a
_consequence_; the actual invariant is that PM stops recognising itself. Anyone who stops at 28 → 14 will chase
directory layout instead of the name match.

## Fix applied 2026-08-10

`_iter_repo_docs()` now also skips `repo_dir` when `repo_dir.resolve() == PM.resolve()` — exclusion by IDENTITY rather
than by name. The existing name-based `_EXCLUDED_REPOS` / `_is_scratch_clone` matching stays for FOREIGN directories,
where the docstring's "the directory NAME is the only signal available at this level" is genuinely true. It is not true
for PM, which knows its own path via the module-level `PM`.

Precedent: the same function already carries two prior name-based patches for this class — `-agentwork-` clones
(2026-07-30) and `.stale-pre-history-rewrite-` backups (2026-08-05). Both were foreign directories, so name-matching was
the right fix there; this one was PM itself, so it was not.

## Residual — NOT fixed here

A PM worktree still cannot run the FULL gate: its `.venv` lacks the sibling-repo installs, so the pytest phase dies with
`No module named 'unified_api_contracts'` (10 failed / 4 errors) and coverage lands under `MIN_COVERAGE=69`. That is a
provisioning gap, not a correctness bug, and the honest guidance is: **run PM's full quality gate from the real
`unified-trading-pm` checkout, not a worktree.** Worktrees remain correct for the ship scripts, which run `prek`, not
the full gate.

- [ ] [INFRA] P3. **Make PM's `quality-gates.sh` fail FAST and clearly when run from an unprovisioned checkout, instead
      of surfacing it as ~10 unrelated test failures plus a coverage miss.** Detect a missing `LOCAL_DEPS` import
      (`unified_api_contracts`) up front and say "PM's full gate needs a provisioned workspace — run it from the real
      checkout; worktrees support prek/ship scripts only." **Done when**: running the gate from a bare worktree prints
      that one line and exits, with no misleading downstream failures.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:2bc91842138bdce6]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. Sole open todo is a precisely-scoped code fix (detect missing `LOCAL_DEPS` import
  up front, print one clear line, exit) with an explicit done-when; root cause already diagnosed and the primary fix
  already shipped. No conflict found against the active corpus.
- **2026-08-19** (`/plan-reconcile security_and_cross_cutting_master` Phase 1, contradiction fix, independently
  corroborated by 2 separate hunter batches): the RECLASSIFY_WHOLE decision above was never actually applied to
  frontmatter — `assigned_vm`/`execution_scope` still read `NA`/`local-only` 2 days later, silently keeping the sole
  open todo out of the AO backlog despite the audit's own explicit, reasoned decision to dispatch it. Applied the
  frontmatter flip this pass (`assigned_vm: planning`, `execution_scope: orchestrator-agent`) — mechanical, the
  judgment call was already made and documented above, just never landed.

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
