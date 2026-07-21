---
doc_type: issue
title: PM quality-gates.sh RED — evidence-backed-completion sub-rule B false positive (31 > baseline 30)
summary: >-
  unified-trading-pm's quality-gates.sh evidence-backed-completion check (sub-rule B) regressed 30 -> 31 from a
  false-positive regex match on `deployment_alerts_ingestion_completeness_2026_07_20.md:160` — the todo mentions a
  workflow FILENAME (`cloud-build-router.yml`) and an unrelated `quality-gates.sh` "green" claim, not an actual
  Cloud-Build-success claim, but the checker's loose regex (any `cloud[- ]build` substring + any `green`/`SUCCESS` token
  anywhere in the block) flags it anyway. Blocks the green-tree ship gate for any non-`docs(plans):` PM commit.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, evidence-backed-completion, governance, false-positive]
related: [pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
resolved_by: slot-4
locked_by:
source: [pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

Running `bash scripts/quality-gates.sh` in `unified-trading-pm` (needed to ship an unrelated plan-discipline
banner-sweep fix, see `pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`) fails on
`check_evidence_backed_completion.py` sub-rule B: 31 violations vs the committed baseline of 30.

Root cause traced via `git stash` (confirmed pre-existing on a clean tree, unrelated to my staged diff) + bisection
against the commits I fast-forward-pulled mid-session: the new offender is `unified-trading-pm@60b6d855f` ("docs(plans):
flip todo 4 (deployment-api@04b19bd5, unified-trading-pm@36db2e858)"), which flipped a checkbox at
`plans/active/deployment_alerts_ingestion_completeness_2026_07_20.md:160`:

```
- [x] ✅ [BACKEND] P0. **Fix the emitting-vs-subject repo defect** — populate `subject_repo` distinctly from the
      emitting repo on the GHA/ci-failures path, so repo filtering returns correct results. — `deployment-api@04b19bd5`:
      ...
      `unified-trading-pm@36db2e858`: ... threaded the actual subject through at every confirmed cross-repo caller:
      `ci-status-update.yml` ..., `cascade-qg-ordering.yml` ..., `escalate-to-orchestrator.yml`,
      `publish-package.yml`, `cloud-build-router.yml` (9 call sites), ...
      `quality-gates.sh` green in both repos (a pre-existing, unrelated repo-wide QG red — `plan-discipline`
      regression + a missing ...
```

This is a genuine code-ship claim (`<repo>@<sha>` + "QG green in both repos"), evidenced exactly the way the checker's
own docstring says sub-rule B should NOT fire for ("deliberately NOT... code-ship claims... evidenced by the commit +
local QG sentinel, not a build-id" — `check_evidence_backed_completion.py` lines 60-64). But `_RUNTIME_VERB_RE` matches
the literal substring `cloud-build` inside the **workflow filename** `cloud-build-router.yml` (one of 9 GHA callsites
this todo threads a fix through — not a claim that a Cloud Build ran), and `_GREEN_TOKEN_RE` separately matches the
unrelated `quality-gates.sh` "green" mention a few lines later in the same multi-line todo block. Neither token is
actually about a Cloud Build going green — the AND-of-two-unrelated- substrings-anywhere-in-the-block heuristic produces
the false positive.

# Why it matters

Same blast radius as the sibling plan-discipline issue: `unified-trading-pm`'s `quality-gates.sh` gates every
non-`docs(plans):` quickmerge ship through this repo. With ~50+ backlog tasks draining concurrently, a false-positive
ratchet regression here silently blocks anyone who needs a normal PM commit to ship, even when their own diff has
nothing to do with the offending todo.

# Recommended decision

- Immediate unblock (low-risk): `--baseline-write` to codify 30 -> 31, since this is a verified false positive (not
  missing evidence) and the check's own error message names this as its self-service remedy for "intentional debt"
  cases. A worker should NOT self-authorize this without checking whether an operator-sign-off norm applies to this gate
  too (the sibling plan-discipline issue had an explicit "HOLD — do NOT run --baseline-write yourself yet" from the
  operator on a similarly-shaped ratchet-raise) — flag for one operator glance before writing it.
- Real fix (more durable): tighten `_RUNTIME_VERB_RE`/`_GREEN_TOKEN_RE` in `check_evidence_backed_completion.py` to
  require the runtime-verb and green-token to appear in the SAME sentence/clause (or within N chars of each other)
  rather than anywhere in the whole multi-line todo block — this is the same "regex matches an incidental substring
  inside unrelated prose" false-positive class documented in
  `pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md` for `check_plan_discipline.py`'s DEFERRED-token
  regex. Needs a fleet-wide re-scan after the regex tightens (could surface fewer OR reveal previously-masked real
  violations elsewhere — re-baseline whichever way it moves).

## Todos

- [x] [DOCS] P2. ✅ Get operator sign-off on `--baseline-write` — HOLD received (BLK-9c18d1a3): operator/main declined
      the baseline-up path ("baselines only go DOWN" + moving a shared repo-wide integrity gate up to absorb a false
      positive is fleet-impacting) and directed the P3 root-cause fix below instead, with the guardrail that the
      tightened regex must not introduce new false negatives. No `--baseline-write` up was run. (repo:
      unified-trading-pm)
- [x] [SCRIPT] P3. ✅ Tightened `_RUNTIME_VERB_RE` + `_GREEN_TOKEN_RE` co-occurrence in
      `scripts/quality_gates/check_evidence_backed_completion.py` sub-rule B to require SAME-CLAUSE proximity (new
      `_CLAUSE_BOUNDARY_RE` splits on `.`/`!`/`?` + whitespace + capital/backtick, collapsing line-wraps first) instead
      of whole-block presence — unified-trading-pm@8c7613218. Re-scanned the full plan corpus (no `--include-issues`,
      matching the exact QG invocation): 31 → 21 violations (baseline 30). Verified all 10 items that dropped out (the
      target false positive + 9 more of the same shape) are genuine false positives, not new false negatives — for each,
      traced the exact verb/green match pair and confirmed it was either an exempted code-ship `QG-green` mention, a
      hypothetical/counterfactual clause ("a silent-success path **would have**..."), a future-tense TODO, or a
      filename/job-name token (`cloud-build-router.yml`, `dispatch-cloud-build`) paired with an unrelated green mention
      elsewhere in the block — none were an actual runtime-green claim losing its flag. Confirmed genuine same-clause
      claims (real over-claims) still get flagged via `tests/unit/test_check_evidence_backed_completion.py` (8 new
      tests: 4 false-positive-shape fixtures now clean, 4 genuine-claim fixtures still flagged, incl. one that spans a
      line-wrap but not a real sentence boundary, and one Evidence-ref-suppression sanity check). Re-baselined 30 → 21
      via `--baseline-write` to codify the improvement (a real fix-driven count drop, not a ratchet-up — needs no
      operator sign-off per the HOLD guidance). Full `quality-gates.sh` green (sentinel = HEAD). (repo:
      unified-trading-pm)
