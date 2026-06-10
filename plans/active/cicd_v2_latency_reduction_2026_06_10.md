---
title:
  "CI/CD v2 latency reduction — parallelise the monolithic QG step + content-sentinel skip of redundant stage re-runs"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
locked_by: live-defi-rollout
created: 2026-06-10
source:
  - operator 2026-06-10 ("this is really slow, barely committing code, ~12 min per attempt and per repo")
  - measured: execution-service v2 = 12m58s, of which the single "Run quality gates" step = 715s; cross-repo is
    ALREADY parallel (3 v2s in-flight concurrently); the cost is within-repo
related:
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

# CI/CD v2 latency reduction

> **Problem (measured 2026-06-10):** one change takes ~36-48 min to reach `main` because the **same ~12-min
> `quality-gates-v2` runs 3-4× serially** across the promotion stages (LDR→staging PR + post-merge push, then
> staging→main PR + post-merge push), and the 12 min is **one monolithic serial `quality-gates.sh` step** (the "Run
> quality gates" step = **715s of 778s total**; clone/install/setup are ~50s combined). **Cross-repo is already
> parallel** (GH Actions runs each repo's v2 on its own runner — 3 confirmed in-flight). So the levers are NOT
> batching-across-repos; they are: **(A) parallelise the fat step**, **(B) shard pytest**, **(C) stop re-running the
> full gate on byte-identical content**.

## Success criteria

- A single repo's `quality-gates-v2` wall-time drops from ~12 min to **~6-8 min** (sum → slowest-parallel-component).
- A change reaching `main` runs the **full gate at most twice** (not 3-4×) — redundant re-runs on an already-green
  content-SHA are skipped.
- **Fleet `main` stays 25/25 green throughout** — prove the speedup AND the correctness on ≥1 consumer repo before any
  fleet roll (rule 11: a gate change is not done until proven on a CONSUMER, not just PM).
- No coverage lost: every check that ran in the monolithic step still runs (just in parallel).

## Phases

### Phase 1 — Split the monolithic QG step into PARALLEL jobs (the biggest win) — P1

- [ ] [SCRIPT] P1. In `scripts/workflow-templates/quality-gates-v2.yml.tmpl`, replace the single `quality-gates.sh`
      invocation with a **job matrix / parallel jobs** that each run a SUBSET via the existing flags: `tests`
      (`--test`), `typecheck` (`--skip-tests --skip-lint`), `lint+codex` (`--lint`), `pip-audit` (its own slice). Each
      job: checkout + the cheap setup (~50s) + its slice. The required-check **context name stays
      `Quality Gates (<repo>) / quality-gates-v2`** — branch protection matches on it, so the job `name:` / aggregation
      gate must preserve that exact context (use a final `needs:`-all aggregation job that reports the required context,
      or set the required check to the matrix's rollup). Wall-time → `max(slice)` not `sum(slices)`. Verify the QG
      SENTINEL is still written on full-green (quickmerge `--agent` depends on it) — the sentinel must key off ALL
      slices passing. Repo: unified-trading-pm (template) → fleet rollout.
- [ ] [SCRIPT] P2. Ensure the base scripts (`base-service.sh` / `base-library.sh`) support clean slicing — the flags
      (`--test`/`--lint`/`--skip-tests`/`--skip-lint`/`--skip-typecheck`) already exist; confirm each slice is
      self-contained (e.g. pip-audit + codex don't depend on the tests slice's state) and that a sliced run writes a
      PARTIAL sentinel that the aggregation gate combines (do NOT let a partial slice write `.qg_last_passed_sha` = HEAD
      on its own — that already-guarded "partial run detected" path must hold). Repo: unified-trading-pm.

### Phase 2 — Shard / parallelise pytest within the tests slice — P1

- [ ] [SCRIPT] P1. If tests dominate the 715s (measure first — `pytest --durations`), run `pytest -n auto` (xdist is
      already a dep) on a larger runner, and/or shard the test suite across N matrix legs (`--shard`/`-k` partition).
      Keep `pool=forks`-style isolation + `--block-network`. Measure the before/after on the heaviest repo
      (execution-service / strategy-service / mtds). Repo: unified-trading-pm (base scripts) + per-repo if needed.

### Phase 3 — Content-sentinel skip of redundant stage re-runs — P1

- [ ] [SCRIPT] P1. v2 triggers on BOTH `push` AND `pull_request` to `main`+`staging`, so a change runs the full gate up
      to 4× on byte-identical content (PR-v2 then post-merge-push-v2, at each of staging and main). Add a **content-SHA
      sentinel**: if `quality-gates-v2` already passed for this exact tree-content (a content hash, not the commit SHA —
      survives squash/promote re-SHA), **short-circuit the run to GREEN in seconds** (report the required context, skip
      the work). Reuse the existing `.qg_content_sentinel` concept (CLAUDE.md references it). Must NOT skip when content
      actually differs; must still produce the required-context check so the PR isn't BLOCKED. Kills ~2 of the 3-4
      serial 12-min runs. Repo: unified-trading-pm.

### Phase 4 — SIT only on real breaking changes — P2 (mostly DONE, verify)

- [ ] [SCRIPT] P2. Breaking detection is already content-based (`detect_breaking_change.py`: exports/signatures/fields/
      routes/Enum-members) + the bounded-scan baseline fix (this session) eliminated the spurious all-history `feat!`
      trigger. VERIFY a non-breaking promotion (minor/patch, no public-surface change) does NOT fire SIT/cascade-lock on
      a real run, and document the residual (a `feat!:` still short-circuits to breaking by design). No new code unless
      a gap surfaces. Repo: unified-trading-pm.

## Rollout + proof (rule 11 — prove on a CONSUMER, not just PM)

- [ ] [SCRIPT] P1. After Phase 1-3 land on the PM template:
      `rollout-workflow-templates.sh --template     quality-gates-v2.yml.tmpl` to a CANARY consumer first (e.g.
      execution-service), trigger a v2, and prove (a) wall-time dropped, (b) the required context still reports, (c)
      green is still green / a real failure still reds. THEN roll fleet-wide + drive each to main. Do NOT enable a
      stricter/changed gate fleet-wide without the consumer proof.

## Codex SSOT updates

`codex/06-coding-standards/quality-gates.md` (parallel-jobs structure + the content-sentinel skip),
`codex/08-workflows/ci-cd-flow.md` (v2 stage model: full gate runs ≤2× per change, redundant re-runs short-circuited).

## Progress Log

<!-- append-only; autonomous implementer journals here -->
