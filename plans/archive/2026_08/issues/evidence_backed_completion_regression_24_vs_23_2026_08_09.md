---
doc_type: issue
title: evidence-backed-completion sub-rule B regressed 23->24 accidental — blocks quickmerge on unified-trading-pm
summary: >-
  `check_evidence_backed_completion.py`'s sub-rule B (runtime-green claims without an `Evidence: cloudbuild=<id>`
  citation) regressed from its baseline of 23 to 24 sometime before 2026-08-09T09:5x-ish, blocking Pass-1 QG (and
  therefore quickmerge) for every unified-trading-pm commit regardless of `--files` scope, since this is a corpus-wide
  re-scan. Confirmed pre-existing (not caused by my own staged change, which only touched
  `scripts/quality_gates/ao_dispatch_visibility_baseline.yaml`) via a fresh `origin/live-defi-rollout` rebase + re-run.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [evidence-backed-completion, ratchet-regression, ci-cd, blocking, quickmerge]
related: []
created: 2026-08-09
last_updated: 2026-08-09
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
  checker false-positive narrowed (unified-trading-pm@c9b1b6016) + missing Cloud Build citation added
  (unified-trading-pm@<todo-2-sha>) + baseline ratcheted 24->14 (this commit)
context_scope:
  [
    /scripts/quality_gates/check_evidence_backed_completion.py,
    /scripts/quality_gates/evidence_backed_completion_baseline.yaml,
  ]
---

> **ARCHIVED 2026-08-09** — all 3 todos resolved: checker false-positive narrowed, missing Cloud Build citation added,
> baseline ratcheted 24→14. Original path:
> `plans/active/issues/evidence_backed_completion_regression_24_vs_23_2026_08_09.md`.

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

- [x] ✅ [DEVOPS] P1. **CONFIRMED scope false-positive, checker narrowed — unified-trading-pm@c9b1b6016.** Root-caused
      the exact trigger with the checker's own `_iter_todo_blocks`/`_split_into_clauses`: the file moved to
      `plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md` (line 122→128 after the
      archive-banner insert), and the flagged clause is the D5-3 sub-bullet "F3 **success-reporting** — 12+ services'
      `` `cloudbuild.yaml`/`buildspec.aws.yaml` `` `service-deployed` dispatch". Neither token asserts a runtime-passing
      outcome. The `` `cloudbuild.yaml` `` mention is a bare filename reference (the consumer file batch-5 todo 1 owns).
      "Success-reporting" is a named dispatch mechanism used 17x across 7 corpus docs — not a claim of any outcome.
      `_GREEN_TOKEN_RE`'s plain `\b` treated the hyphen in "success-reporting" as a word boundary, so it matched the
      substring as a standalone token. The block never asserts a Cloud Build, deploy, or promote reached a passing state
      anywhere in its ~60-line body (only `<repo>@<sha>` code-ship citations, exempt by design). Narrowed
      `_GREEN_TOKEN_RE` to `(?<!-)\b(?:green|SUCCESS|succeeded)\b(?!-)` (hyphen-guarded both sides) in
      `scripts/quality_gates/check_evidence_backed_completion.py`, added a regression fixture
      (`test_hyphenated_success_reporting_compound_term_not_flagged`) to
      `tests/unit/test_check_evidence_backed_completion.py` mirroring the exact flagged text shape. Verified: existing
      15 tests still pass + new one passes (16/16); re-ran the full corpus scan post-fix — sub-rule B dropped 24→19
      (this fix alone resolved several other "success-reporting"/similar-compound false positives corpus-wide, not just
      this one file); sub-rule A unchanged at 0. Did NOT re-baseline (`--baseline-write`) — that is this doc's own todo
      3, gated on both todos 1 and 2 landing. Repo: unified-trading-pm.
- [x] ✅ [DEVOPS] P1. Investigate `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:171` — determine whether
      `instruments-service@cad1d322`'s deploy to prod has a resolvable Cloud Build id (check
      `gcloud builds list --filter` around the commit's landing time, or the deploy workflow run for that sha). If
      found, add `Evidence: cloudbuild=<id>` to the todo. If the claim is actually evidenced by the cited prod
      scheduler-run success logs rather than a Cloud Build deploy (i.e., no separate build step applies), reword to
      avoid the runtime-green trigger phrase, or confirm with whoever owns the checker whether scheduler-run evidence
      should count as an accepted evidence class. Repo: unified-trading-pm. — **Genuine gap, found + resolved**: the
      `instruments-service-build` Cloud Build trigger (id `2a7fe0d0-cae8-4731-9c2b-0dbf76a6f04c`, region
      `asia-northeast1`, project `central-element-323112`) DOES have a resolvable build for this commit —
      `gcloud builds list --filter='createTime>="2026-08-09T07:55:00Z" AND createTime<"2026-08-09T08:20:00Z"'` surfaced
      build `00f77c23-2ce0-4371-b203-8cedbede3404`, `gcloud builds describe` confirmed status=SUCCESS,
      substitutions.COMMIT_SHA=`cad1d3226f123308632a8608ebd1d18ecb3cb904` (matches the cited `cad1d322` short-sha),
      BRANCH_NAME=`live-defi-rollout`, createTime=2026-08-09T08:02:25Z. Added
      `Evidence: cloudbuild=00f77c23-2ce0-4371-b203-8cedbede3404` to the todo block in
      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` — unified-trading-pm@(this commit). Re-ran
      `check_evidence_backed_completion.py` post-fix: sub-rule B dropped to 20 claims-without-evidence (well under the
      baseline of 24; this specific line no longer appears in the violation list), sub-rule A 0 violations (cited build
      resolves SUCCESS).
- [x] ✅ [SCRIPT] P2. Once both todos above land (or are confirmed false-positive and reworded), re-run
      `check_evidence_backed_completion.py --baseline-write` to ratchet `claim_without_evidence_baseline` back down to
      the resolved count — never leave the baseline absorbing this regression once it's addressed. Repo:
      unified-trading-pm. — **DONE 2026-08-09 (cicd-worker slot 32)**: fresh-pulled `origin/live-defi-rollout`
      (`ec741cc1a`), re-ran `check_evidence_backed_completion.py` clean: sub-rule B now at 14 claims-without-evidence
      (well under baseline 24), sub-rule A 0 violations. Ran `--baseline-write` to ratchet
      `claim_without_evidence_baseline` 24→14 in `scripts/quality_gates/evidence_backed_completion_baseline.yaml`. Issue
      fully resolved — all 3 todos now `[x]`.

## Progress Log

- **cicd-worker slot 17, 2026-08-09**: filed while blocked shipping an unrelated baseline-ratchet fix
  (`ao_dispatch_visibility_gate_regression_34_vs_26_2026_08_09.md`'s final P3 todo). Diagnosed the 23→24 delta down to 2
  new claims + 1 resolved claim (see Evidence above); did not attempt to fix inline — both new claims need domain
  investigation (checker-scope judgment call / cross-repo Cloud Build history lookup) beyond a small/clear fix. Declared
  repo-blocker `qg_red` for unified-trading-pm citing this doc.
- **data_engineering-worker slot 13, 2026-08-09**: resolved todo 2 (the `cad1d322` Cloud Build lookup — see checkbox
  above for full evidence). Left todo 1 (`ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md:122`) untouched — out
  of this task's scope — but note for whoever picks it up: a fresh `check_evidence_backed_completion.py` run post-fix no
  longer lists that line among the 20 remaining claims-without-evidence either, so it may already be resolved/reworded
  by another slot; verify before re-investigating. Todo 3 (baseline-write) intentionally left open per its own stated
  gate ("once both todos above land") even though the corpus is currently green (20 < baseline 24) — re-baselining is
  that todo's own scope, not bundled into this one.
- **cicd-worker slot 2, 2026-08-09**: resolved todo 1 — confirmed scope false-positive per slot 13's own note above,
  root-caused it independently to the `_GREEN_TOKEN_RE` hyphen-boundary bug and narrowed the regex (see checkbox above
  for full evidence) rather than just rewording the one flagged doc, since the same compound-term shape recurs across
  the corpus (17 hits of "success-reporting" alone). Shipped `unified-trading-pm@c9b1b6016` via the standard Pass-1 QG →
  quickmerge flow. Both todos 1 and 2 are now `[x]`; todo 3's gate is clear for whoever picks it up next (not bundled
  into this task).
- **cicd-worker slot 32, 2026-08-09**: resolved todo 3 (the gated baseline-write). Both prior todos were confirmed
  landed, corpus scan clean at sub-rule B=14 (< baseline 24), sub-rule A=0. Ratcheted `claim_without_evidence_baseline`
  24→14. All 3 todos now `[x]` — this issue is fully resolved and eligible for archival per the
  plan-completion-and-archival-discipline SSOT.
