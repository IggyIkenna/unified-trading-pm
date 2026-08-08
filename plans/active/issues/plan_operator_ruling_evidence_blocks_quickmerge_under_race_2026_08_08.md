---
doc_type: issue
title:
  "plan-operator-ruling-evidence post-gate regression (76→84, growing) turns every quickmerge push-race into a hard
  failure on this branch"
summary: >-
  check_plan_operator_ruling_evidence.py's shrinking-ratchet baseline is at 76 known_broken; the live corpus is at 84
  and climbing (confirmed twice in ~15min during a single docs_reconciler session: 83 then 84), spread across 8+
  unrelated plan files (ao_open_issues_consolidated_close_out, bucket_iam_write_protection_per_tier,
  cefi_consolidated_closeout, cross_cutting_satellite_ao_dispatch_batch1/1b, deepseek_flash_ab_routing_test, etc.) — a
  genuine pre-existing plans-corpus regression, not fabricated drift. This is normally a report-only ratchet miss (the
  quality-gates.sh sentinel is written by base-service.sh BEFORE this post-gate check runs, so a clean single-shot
  `quickmerge --agent` still ships fine). But `unified-trading-pm` is under heavy commit contention right now (multiple
  docs(plans) pushes landing every 1-3 minutes from other slots), and quickmerge's own STAGE 0.4 "not-behind gate" pulls
  + rebases on EVERY invocation where origin has moved. Any rebase invalidates the just-written sentinel and forces
  quickmerge's internal retry-regate loop (`_qm_check_agent_sentinel` / `scripts/quickmerge.sh:1604-1635`), which checks
  quality-gates.sh's raw exit code (not just the sentinel file) — and that exit code is unconditionally 1 while this
  check stays red. Net effect: under the branch's current contention level, a scoped, unrelated, fully-green docs fix
  cannot land via quickmerge whenever it loses even one push-race during its run — reproduced twice in a row this
  session (commits 910b8f554 and ad30b8181/b887138, both otherwise-clean docs-only changes to
  codex/06-coding-standards/data-catalogue-schema.md + codex/02-data/service-shard-status-catalogue.md).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    quality-gates,
    quickmerge,
    plan-hygiene,
    operator-ruling,
    ratchet,
    sentinel,
    race-condition,
    plan_operator_ruling_evidence,
  ]
related:
  [
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-08
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: plan_reconciler
drift_direction: advance-process
resolved_by:
locked_by:
source:
  "docs_reconciler one-shot session (slot 16, 2026-08-08) — confirmed via two consecutive real (non-race) quickmerge
  --agent failures shipping an unrelated codex-doc fix, plus standalone
  scripts/quality_gates/check_plan_operator_ruling_evidence.py runs before/after (83 then 84 vs baseline 76)"
---

# plan-operator-ruling-evidence regression blocks quickmerge under push-race contention

## What's actually broken

Two independent things compound into a real ship-blocker:

1. **The ratchet itself has regressed and is still climbing.** `check_plan_operator_ruling_evidence.py` baseline is 76
   `known_broken` unsourced `'operator ruling'` citations; the live corpus measured 83 at ~13:55Z and 84 at ~14:10Z in
   this same session — 8 new unsourced citations landed across at least 8 different plan files in the last few days,
   none touched by this session. This is out of scope for `docs_reconciler` (plans-corpus discipline is
   `plan_reconciler`'s territory per `.claude/skills/docs-reconcile/SKILL.md` "Out of scope" section) but is reported
   here because of (2).

2. **`quickmerge.sh`'s retry-regate loop treats the check as an unconditional gate, not a ratchet, mid-run.** The
   `.qg_last_passed_sha` sentinel is written by `base-service.sh` BEFORE post-gate checks run (confirmed by reading
   `scripts/quality-gates.sh` lines ~419-991), so a single clean `bash scripts/quality-gates.sh` + immediate
   `quickmerge --agent` with **zero** intervening origin pushes ships fine even with this check red — the sentinel
   SHA-match fast path (`_qm_check_agent_sentinel`, `scripts/quickmerge.sh:1542-1590`) never inspects the check's
   result. But `unified-trading-pm`'s current commit rate means STAGE 0.4 ("not-behind gate") almost always finds origin
   has moved during a multi-minute quality-gates run, triggers a rebase, invalidates the sentinel, and enters the
   bounded retry loop (`scripts/quickmerge.sh:1602-1635`). That loop's re-gate step is:
   `if ! bash scripts/quality-gates.sh --no-fix $SKIP_CODEX; then echo "Re-gate FAILED..."; exit 1; fi` — it checks the
   script's raw exit code, not the sentinel file the script also wrote. Since this one post-gate check keeps the overall
   exit code at 1 regardless of the diff being shipped, **any quickmerge run that needs even one internal re-gate
   currently cannot succeed**, full stop — not a flaky race, a deterministic outcome given the check's current red
   state.

## Evidence

- Commit `910b8f554` (codex-only docs fix) → `quickmerge --agent` → STAGE 0.4 pulled in `9877120e4` mid-run → retry-
  regate → `❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.` (task `b5ik2e34y`
  output, line 80-81).
- Re-gated fresh against the new HEAD (`ad30b8181`, sentinel confirmed byte-matching HEAD), immediately re-ran
  `quickmerge --agent` → STAGE 0.4 pulled in `fa4b010ac` mid-run (yet another new commit) → rebased to `b887138` → same
  failure class (full pre-flight + gate output before truncation, sentinel-file re-verified matching `b887138` post-run,
  exit code 1 overall).
- `check_plan_operator_ruling_evidence.py --workspace-root <root>` run standalone against current HEAD: **84 > baseline
  76**, listing 8+ distinct plan files, none related to either failed commit's diff.

## Why this matters beyond one docs fix

This is a **shared PM-repo bottleneck**, not specific to `docs_reconciler`: any agent shipping any scoped, correct,
fully-green (by sentinel) change to `unified-trading-pm` is subject to the same race whenever origin moves during their
gate run — which, per the evidence above, is close to guaranteed right now given the branch's commit cadence. The
script's own comments (`scripts/quickmerge.sh:1536-1540`) already document a precedent
(`quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21`, "up to 27 consecutive full-QG losses
observed... under heavy PM doc-push contention") — that incident's fix (auto re-pull + re-gate + retry) assumed the
re-gate would eventually succeed once the tree stabilized. It does not, while this specific post-gate check stays red:
the re-gate can succeed at writing a fresh sentinel and still report exit 1, because the check's failure is
tree-content-based (real plan citations), not tree-motion-based (a transient race) — the retry loop has no way to tell
these apart because it only reads the aggregate exit code.

## Options (recommendation first)

1. **(Recommended) Fix the plans-corpus regression** — `plan_reconciler`'s natural remit: add a traceable
   `/plans/…`/`/codex/…` source reference within 300 chars of each of the 8 offending `'operator ruling'` citations (or
   confirm+re-baseline via `--baseline-write` only for entries that trace to a genuinely undocumented-but-real ruling,
   per the standard in `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` § "Done when"). This clears the
   root cause without touching quickmerge's retry semantics.
2. **Fix `quickmerge.sh`'s retry-regate to re-check the sentinel file after a re-gate, not the script's raw exit code**
   — the re-gate's PURPOSE is "did the sentinel become valid for the new HEAD", which is answerable directly
   (`_qm_check_agent_sentinel` again) without conflating it with "are ALL corpus-wide ratchets green". This is a
   quickmerge behavior change and needs an operator/infra-owner decision since the comment history shows this exact loop
   has already been tuned three times under incident pressure (2026-07-16/18/21) — do not re-tune it unilaterally.
3. **Do nothing / accept as known limitation** — not recommended: the branch's commit cadence means this will keep
   recurring for every agent, not just this session.

## Done when

Either the ratchet is back at/below baseline (option 1) or the retry-regate logic is fixed to not conflate "sentinel
valid for new HEAD" with "every post-gate ratchet green" (option 2), with the reasoning + operator sign-off recorded
here.
