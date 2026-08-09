---
doc_type: issue
title:
  sync-gitignore-cursorignore.py is silently destructive — the central .gitignore template has drifted behind PM's
  actual file, and --dry-run does not skip writes
summary: >-
  While fixing a small, unrelated finding (4 stray empty gitlinks under `.claude/worktrees/` in unified-trading-pm,
  causing a harmless-but-noisy "No url found for submodule path" warning on every CI checkout of PM), I added one new
  pattern to `scripts/templates/.gitignore.central` and ran `sync-gitignore-cursorignore.py --dry-run` to preview the
  fleet-wide propagation before deciding whether to ship it broadly. Two things went wrong: (1) `--dry-run` does NOT
  gate the actual file writes — it fully overwrote `.gitignore`/`.cursorignore` in all 24 sibling repos + PM itself, and
  its own `untrack-ignored-files.py --untrack` sub-step then actually removed several REAL, currently-tracked files from
  6+ repos' git index (still present on disk, just untracked — no data was physically lost, but this was one `quickmerge
  --agent` away from silently dropping real production files — e.g. deployment-ui's capability-manifest loader/JSON,
  unified-trading-system-ui's entire `app/(platform)/services/data/*` page tree, strategy-service's data loader module —
  from tracking fleet-wide). (2) Separately, PM's own live `.gitignore` has substantial PM-specific accumulated fixes
  NOT reflected in the checked-in `scripts/templates/.gitignore.central` (QG-sentinel patterns with rationale comments,
  `!plans/audit/results/*.csv` audit-artifact exemptions, the `cursor-configs/settings.json` re-tracking fix from
  `/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md`, the `harsh_orchestrator/backlog.yaml`
  defensive ignore, etc.) — the full-rewrite sync would have silently REGRESSED all of these already-shipped, documented
  fixes had I committed it. Caught before any commit/push; reverted every repo's accidental `.gitignore`/`.cursorignore`
  change and every accidentally-untracked file (re-`git add`'d by exact name, content unchanged, confirmed via
  zero-diff) via a full 24-repo `git status` sweep. Shipped only the narrow, intended fix by hand (2274aa963): the 4
  gitlink removals + a single new `.claude/worktrees/` stanza added directly to both PM's `.gitignore` and the central
  template (NOT via the sync script).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [gitignore, sync-script, destructive, tooling-bug, template-drift, near-miss]
related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]
created: 2026-07-27
author: unknown
priority: P2
parent_epic: infrastructure_master
source: "Discovered while shipping an unrelated small fix (stray .claude/worktrees/ gitlinks), 2026-07-27 ~21:15 UTC"
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    scripts/workspace/sync-gitignore-cursorignore.py,
    scripts/templates/.gitignore.central,
    scripts/workspace/untrack-ignored-files.py,
    /plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md,
  ]
resolved_by:
---

# `sync-gitignore-cursorignore.py` is unsafe to run today — two compounding bugs

## What I found

**Bug 1 — `--dry-run` does not actually preview; it writes for real.** Running
`.venv/bin/python scripts/workspace/sync-gitignore-cursorignore.py --dry-run` from PM fully rewrote `.gitignore` (and
created/modified `.cursorignore`) in all 24 sibling repos plus PM itself — confirmed via
`git status --short .gitignore .cursorignore` per repo immediately after, all showing real, uncommitted diffs. The
script's own printed output even said `Updated <repo>/ (.gitignore, .cursorignore)` and `Done. Synced 25 repos.` — not
"would update". The flag appears to only gate the separate, explicitly-documented `--purge-history` destructive path,
not the base sync write.

**Bug 2 — the write includes an automatic untrack step that deleted real tracked files from the index.** The script's
own tail output shows it chains into `untrack-ignored-files.py --untrack` unconditionally. Because the full-rewrite
`.gitignore` differs structurally from several repos' existing files (broader generic patterns replacing repo-specific
ones), previously-tracked real files newly matched an ignore pattern and got `git rm --cached`'d. Confirmed via
`git status --short` across the fleet immediately after the dry-run, `D `-flagged (deleted from index, present on disk)
in: `agent-orchestrator` (4 files under `data/config/`), `strategy-service` (2 files under
`strategy_service/engine/data/`), `unified-api-contracts` (4 files under `unified_api_contracts/{canonical,registry}/`),
`unified-trading-api` (3 PDF sample reports), `unified-trading-system-ui` (34 files — nearly its entire
`app/(platform)/services/data/*` and `components/data/*` page/component tree, plus `.env.production`,
`.vscode/ settings.json`, two `.pptx` files, one `.pdf`), `deployment-ui` (4 files under `src/data/`). All content
verified still present on disk (checked file sizes/mtimes directly) — this was an index-only untrack, not a physical
delete — but had any of these repos' next `quickmerge --agent` run without a human/agent noticing the untracked state
first, the next real commit in each repo would have silently dropped that content from tracking going forward (it would
still exist on whoever's disk currently has it, but a fresh clone would be missing it — the standard "looks fine
locally, breaks for everyone else" untracked-file failure mode).

**Bug 3 (root cause of Bug 2's blast radius) — the central template (`scripts/templates/.gitignore.central`) is stale
relative to PM's own live `.gitignore`.** Diffing what the sync would have produced against PM's actual current file
showed PM has accumulated real, documented, already-shipped fixes that were never synced back into the shared template:
the `*.zip` archive rule, the QG-sentinel/profiler/cache patterns (`/.qg_last_passed_sha` etc.), the generated-artifact
untracking block with its full rationale (SVGs/HTML/manifests, referencing `cicd_contract_hardening_ 2026_06_01` item
H), the `!plans/audit/results/*.csv` and `!plans/audit/results/*.parquet` mega-audit exemptions, the
`!scripts/self-hosted-runners/hosted-baseline/MANIFEST.tsv` provenance exemption, `plan_health_digest.md`/
`plan_skeleton.md` orchestrator-generated ignores, `harsh_orchestrator/backlog.yaml`, and — most notably — the
`cursor-configs/settings.json RE-TRACKED 2026-07-23` fix with its full incident-history comment (see
`/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md`). None of this exists in the checked-in
central template. Running the sync for real today would silently un-fix all of it in PM specifically, on top of whatever
each of the 24 sibling repos has independently accumulated that I did not audit (I only diffed PM's).

## What I did (fully contained, nothing shipped)

1. Reverted every repo's accidental `.gitignore`/`.cursorignore` write via `git checkout -- <file>` (for previously-
   tracked files) or moved the newly-created untracked `.cursorignore` out to scratchpad (for repos that didn't have one
   yet) — 24 repos, zero remaining diff on either file anywhere, verified via a full fleet `git status --short` sweep.
2. Re-`git add`'d (by exact name, never `-A`) every file the untrack step had dropped from 6 repos' indices — content
   was unchanged on disk throughout, so each re-add produced a zero `git diff --cached` against HEAD, confirming no
   content was altered, only the tracking state was restored.
3. `unified-trading-system-ui`'s `.env.production` needed `git add -f` specifically — it's a pre-existing, deliberately
   tracked exception to the general `.env*` ignore pattern (tracked before the ignore rule existed); restored to its
   original tracked state, not a new policy decision.
4. Shipped ONLY the originally-intended, narrow fix by hand — added one new `.claude/worktrees/` stanza directly to both
   PM's live `.gitignore` and `scripts/templates/.gitignore.central` (NOT via the sync script), alongside untracking the
   4 actual stray gitlinks that motivated this in the first place. Commit `2274aa963`. Full fleet `git status` swept
   clean again post-ship (one unrelated pre-existing untracked stray in PM, one unrelated pre- existing untracked report
   dir in instruments-service, both confirmed harmless and pre-dating this session).

## What still needs doing (not done — real work, needs a careful pass)

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-9) — `unified-trading-pm@78a3740bf`.** Fix
      `sync-gitignore-cursorignore.py`'s `--dry-run` flag to actually gate all writes (the base sync AND the chained
      `untrack-ignored-files.py --untrack` call), not just the separately-documented `--purge-history` path. Verified
      live 2026-08-02: `main()`'s write loop (`gitignore_path.write_text`/`cursorignore_path.write_text`) is gated
      behind `if dry_run: ... continue`, and the chained untrack call passes `--dry-run` (not `--untrack`) when
      `dry_run` is set — both paths confirmed gated in the current file.
- [ ] [SCRIPT] P2. **Reconcile `scripts/templates/.gitignore.central` against PM's actual live `.gitignore`** (and
      ideally against a sample of the other 24 repos, since I only audited PM) before this sync script is safe to run
      for real again. This is real diffing/merging work, not mechanical — several of PM's exceptions are clearly
      PM-specific (won't want to blanket-apply to service repos) vs. clearly should-be-central (the QG sentinel
      patterns, the generated-artifact rules, if other repos regenerate the same artifacts) — needs a human or a careful
      per-line judgment call, not a blind template overwrite in either direction.
- [ ] [VERIFY] P3. Once the template is reconciled, re-run `--dry-run` (post-fix) across all 25 repos and manually spot-
      check 3-4 diffs before trusting it enough to actually ship a fleet sync.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. Both remaining `[SCRIPT]`/`[VERIFY]` items still gate on the same real, per-line human diffing/merging
  judgment call (which of PM's accumulated `.gitignore` exceptions are PM-specific vs. should-be-central) this doc's own
  text has described since 2026-07-30; the P3 verify item is dependency-gated behind it. Checked against this round's
  accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default,
  escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks) — none bear on
  a template-vs-live-file reconciliation judgment call.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — template reconciliation is a judgment call
  (which .gitignore is canonical) + post-fix verification sweep; operator/design-flavored, not a bounded flip.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Central remaining item
  (reconciling the template against PM's live .gitignore) is explicitly self-described as real diffing/merging work
  needing human judgment, not mechanical.
- **na-eligibility-audit 2026-08-03** (infra tranche, incremental run, dispatch agt-a41abf): **KEEP-NA, valid —
  unchanged from the 2026-07-30 verdict.** In scope only because a context_scope frontmatter backfill (batch 3/5)
  touched the file since; `git show` confirms the only other diff in that same commit was a pure line-wrap reflow of the
  already-`[x]` item's text (no wording/content change). `grep -cE '^- \[ \]'` = **2**, matching this verdict: the
  template-reconciliation item still needs human diffing judgment, and the dependent P3 verify item is gated behind it.
  No action needed.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — verified all still resolve).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
