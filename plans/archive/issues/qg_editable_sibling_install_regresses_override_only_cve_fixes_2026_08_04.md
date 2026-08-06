---
doc_type: issue
title:
  QG editable-sibling install (uv pip install -e, LOCAL_DEPS) silently regresses override-dependencies-only CVE fixes
summary:
  "base-service.sh's LOCAL_DEPS editable-sibling-install loop runs `uv pip install -e <sibling> --python
  .venv/bin/python` AFTER `uv sync --frozen` — that command is uv's pip-compatible interface, which does NOT read
  `[tool.uv] override-dependencies`, so a sibling whose CVE fix lives ONLY in that section is invisible to it. Confirmed
  live: unified-api-contracts's cryptography>=50.0.0 fix (override-dependencies-only) is silently downgraded back to
  49.0.0 in the CONSUMING repo's local .venv the moment that repo's QG editable-installs unified-api-contracts. 22 of 23
  fleet repos declare LOCAL_DEPS, so this is a fleet-wide local-QG-integrity gap, not PM-specific."
status: resolved # (was: open) 2026-08-06 RB-04f4f852 archival: all todos [x], no locked_by
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, uv, dependency-management, cve, pip-audit, ci-local-parity]
related:
  [
    /plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    /plans/active/issues/orphan_cve_aiohttp_fix_slot5_unpushed_2026_08_03.md,
    plans/archive/2026_08/ci_local_qg_parity_2026_06_08.md,
  ]
created: 2026-08-04
author: slot-9
parent_epic: infrastructure_master
priority: P1
source:
  [
    "2026-08-04 (slot-9) — discovered while shipping unified-trading-pm's own cryptography CVE-2026-69247 bump
    (cve_affected_pinned_deps_remediation_2026_06_18.md): `bash scripts/quality-gates.sh` kept reporting `pip-audit
    vulnerabilities found: cryptography 49.0.0` even immediately after a fresh, manually-verified `uv sync` confirmed
    `.venv` had cryptography 50.0.0 and `.venv/bin/python -m pip_audit` reported clean.",
  ]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-04
context_scope:
  [
    scripts/quality-gates-base/base-service.sh,
    scripts/quality-gates.sh,
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_06/ci_local_qg_parity_2026_06_08.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# QG editable-sibling install silently regresses override-dependencies-only CVE fixes

## What I found

`scripts/quality-gates-base/base-service.sh` (the shared per-repo QG body, sourced by every repo's own
`scripts/quality-gates.sh`) runs, in order:

1. `UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --quiet` — installs the repo's OWN committed `uv.lock` exactly (this
   DOES honor `[tool.uv] override-dependencies`, since `uv sync` is project-mode).
2. For each entry in the repo's `LOCAL_DEPS` array (e.g. `("unified-api-contracts" "unified-trading-library")`):
   `uv pip install -e "$_libcand" --python "$_venv_py" --quiet` — installs the sibling repo in editable mode so its
   source is importable (for basedpyright cross-repo typecheck resolution + any test that imports it).

`uv pip install -e` is uv's **pip-compatible interface**. Unlike `uv sync`, it does **not** read the target package's
`[tool.uv]` section (`override-dependencies`, `constraint-dependencies`, etc.) — that's a project-mode-only concept. It
does a fresh, independent resolve of the sibling's declared `[project.dependencies]` plus whatever's already in the
target environment.

**Confirmed reproduction** (unified-api-contracts's cryptography fix — `unified-api-contracts@ead2eec0` — declares
`cryptography>=50.0.0,<51.0.0` ONLY inside `[tool.uv] override-dependencies`, not in `[project.dependencies]`):

```bash
cd unified-trading-pm
UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --quiet
.venv/bin/python -c "import cryptography; print(cryptography.__version__)"   # 50.0.0 (correct, from PM's own uv.lock)
uv pip install -e ../unified-api-contracts --python .venv/bin/python --quiet
.venv/bin/python -c "import cryptography; print(cryptography.__version__)"   # 49.0.0 (regressed!)
```

Ruled out simpler explanations before concluding this is a real resolver-visibility gap, not an artifact of this
session's venv history:

- **Not stale-cache**: reproduces identically with `--refresh` (forces uv to bypass its resolution/metadata cache).
- **Not `--no-deps` needed on the wrong side**:
  `uv pip install -e ../unified-api-contracts --python .venv/bin/python --no-deps` does NOT regress cryptography (stays
  50.0.0) — confirming the regression is specifically the sibling's OWN transitive-dependency resolution, not something
  about the editable-install mechanism itself.
- **Not contamination from an old venv**: reproduces on freshly-synced `.venv` state (confirmed via repeated
  `uv sync --frozen` immediately before each reproduction).
- **Is fleet-wide, not PM-specific**: `grep -rl "LOCAL_DEPS=" */scripts/quality-gates.sh` matches 22 of 23 repos. Any
  consuming repo that editable-installs a sibling whose CVE fix is override-dependencies-only is exposed the same way —
  PM just happened to be the first repo where a genuinely fresh `.venv` sync exposed it today, because
  unified-api-contracts's cryptography fix (slot-8, today) is very recent.

## Why it matters

- **Silently defeats a shipped CVE fix's local verification**: unified-api-contracts's cryptography>=50.0.0 fix is real
  and correctly shipped (its OWN `uv.lock` says 50.0.0), but any OTHER repo's local `pip-audit` check — the exact
  mechanism meant to catch this class of CVE — reports the PRE-FIX vulnerable version instead, because the
  editable-sibling step silently downgrades it after the frozen-lock install already got it right.
- **Not just a false-positive nuisance** — the inverse (false-negative) is the real risk: if a DIFFERENT, still-open CVE
  existed only in a sibling's plain `[project.dependencies]` (not override-only), the editable-sibling step could just
  as easily pick a vulnerable version the frozen lock had correctly avoided, and pip-audit would then falsely report
  clean depending on install order — this needs verification, not assumed safe just because today's instance happened to
  be a false-positive.
- **Blocks legitimate shipping**: this exact regression is what's currently preventing `unified-trading-pm`'s own
  cryptography CVE-2026-69247 bump from getting a genuine `quality-gates.sh` exit 0 (required by the `--agent`
  quickmerge sentinel) — the shipped `pyproject.toml`/`uv.lock` are independently verified correct
  (`.venv/bin/python -m pip_audit` reports clean immediately after `uv sync` alone, before the editable-sibling step
  runs), but the full script cannot currently produce a trustworthy green run.
- **Widespread surface**: 22 of 23 repos use this LOCAL_DEPS pattern; several fleet repos fixed their own cryptography
  CVE via override-dependencies-only (alerting-service, fund-administration-service, greeks-service, features-service,
  ml-service, instruments-service, unified-api-contracts per `cve_affected_pinned_deps_remediation_2026_06_18.md`'s DONE
  entries) — any of those, when editable-installed as a LOCAL_DEPS sibling elsewhere, could reproduce this same class of
  regression for whichever consuming repo's local QG happens to hit a genuinely fresh sync.

## Recommended decision

Candidate fix directions (none applied — this needs review given the shared blast radius across 22 repos):

1. **Add `--no-deps` to the `uv pip install -e` call in `base-service.sh`'s LOCAL_DEPS loop.** Matches the step's OWN
   stated intent per its existing comments — the goal is making the sibling's SOURCE importable for basedpyright type
   resolution (and whatever tests import it), not re-resolving its runtime dependency graph (which `uv sync --frozen`
   already correctly established for the CONSUMING repo). **Risk to verify first**: several files across the fleet
   `import unified_api_contracts` / `import unified_trading_library` directly in tests — need to confirm `--no-deps`
   doesn't leave any of THEIR transitive imports unresolved (i.e. that the consuming repo's own `uv sync --frozen`
   already provides everything those imports need at runtime, not just for typecheck). Untested by this doc.
2. **Per-repo escape hatch**: for `unified-trading-pm` specifically, basedpyright is fully EXCLUDED already
   (`pm_scripts_typecheck_debt_2026_06_11.md` — `[tool.basedpyright] exclude` includes `"scripts"`, so it analyzes ZERO
   files) — meaning THIS repo's LOCAL_DEPS loop currently serves no live typecheck purpose, only whatever test files
   import UAC/UTL directly. Emptying `LOCAL_DEPS=()` in PM's own `scripts/quality-gates.sh` (a per-repo file, NOT the
   shared base script) would be a zero-blast-radius fix for PM alone — but ~20 files under `tests/`/`scripts/` import
   `unified_api_contracts`/`unified_trading_library` today, so this needs a real check for which of those would break at
   collection time, not just typecheck.
3. **Fix at the source**: repos whose CVE fix is override-dependencies-only could ALSO declare the same floor as a plain
   (non-override) entry wherever it's safe to (e.g. if the package is a genuine direct or near-direct dependency) —
   makes the fix visible to pip-compat consumers too. Doesn't generalize to purely-transitive cases where
   override-dependencies is the only way to force the floor at all.

**RESOLVED 2026-08-04 (slot-12)**: direction 1 (`--no-deps`) was tested and REJECTED — it broke
`unified-api-contracts`'s own `pydantic`-based imports in THIS repo (`tests/unit/test_capability_readiness.py`,
`test_capability_param_schema.py` both import `unified_api_contracts.internal.architecture_v2.capability_manifest`,
which imports `pydantic` at module level; PM's own `pyproject.toml` never declares `pydantic`, so it's only ever
reachable via UAC's normal transitive resolve — confirmed live: `ModuleNotFoundError: No module named 'pydantic'`). The
shipped fix instead extracts each LOCAL_DEPS sibling's `[tool.uv] override-dependencies` into a combined
`--overrides <file>` passed to `uv pip install -e` (a real `uv pip install` flag — requirements-file-style version
overrides, distinct from project-mode `override-dependencies`) — this forces the intended CVE floor while preserving
full normal transitive-dependency resolution. See `base-service.sh@568cd6e17` for the implementation.

Also corrects this doc's own "22 of 23 repos" scope claim: that count came from `grep -rl "LOCAL_DEPS="`, which matches
the empty `LOCAL_DEPS=()` declaration too. Re-enumerated 2026-08-04 across all 25 fleet repos with non-empty-array
detection: only **2 repos** are actually affected — `unified-trading-pm` (`unified-api-contracts`,
`unified-trading-library`) and `deployment-service` (`deployment-api`). Both were validated end-to-end (full
`bash scripts/quality-gates.sh`, genuine exit 0, sentinel == HEAD) with the shipped fix before it landed.

## Todos

- [x] ✅ [SCRIPT] P1. Validate whether `uv pip install -e <sibling> --no-deps` (added to the LOCAL_DEPS loop in
      `scripts/quality-gates-base/base-service.sh`) causes any import failure across the fleet's test suites that import
      `unified_api_contracts`/`unified_trading_library` directly — run each affected repo's full `quality-gates.sh`
      before/after the flag change and diff pass/fail counts. If clean, land the flag change (one shared-script edit) —
      this is the most general fix. (repo: unified-trading-pm) — unified-trading-pm@568cd6e17. Re-enumerated the fleet:
      only unified-trading-pm + deployment-service actually have non-empty LOCAL_DEPS (not 22). `--no-deps` empirically
      broke PM's own `capability_manifest` import (missing `pydantic`) — REJECTED. Shipped a safer `--overrides <file>`
      fix instead (extracts each sibling's `[tool.uv] override-dependencies`, preserves full transitive resolution).
      Both affected repos' full `quality-gates.sh` genuinely pass (PM: 1687 passed/0 failed, pip-audit clean, sentinel==
      HEAD; deployment-service: 3066 passed/0 failed, sentinel==HEAD).
- [x] ✅ [SCRIPT] P2. Once direction 1 (or an accepted alternative) lands, re-verify `unified-trading-pm`'s own
      cryptography CVE-2026-69247 bump gets a genuine `bash scripts/quality-gates.sh` exit 0 (its `pyproject.toml`/
      `uv.lock` changes are already independently verified correct via manual `pip-audit` — this todo is purely about
      confirming the FULL script now agrees). (repo: unified-trading-pm) — confirmed by the SAME Pass-1 run above:
      `.qg_last_passed_sha` == HEAD (568cd6e17), `✅ pip-audit clean` in the log (cryptography correctly at 50.0.0, no
      downgrade).
- [x] ✅ P2. Not needed -- operator ruled it out. (was: Decide whether any OTHER repo's LOCAL_DEPS sibling install has
      already produced a false-negative (silently upgrading a version the frozen lock had correctly pinned LOW for a
      real reason) rather than today's false-positive (downgrading a version the frozen lock had correctly pinned for
      security) — this doc only confirms the mechanism and one concrete false-positive instance; a fleet-wide audit of
      whether the inverse has ALREADY happened silently is a genuine judgment call on priority/scope, not a bounded
      worker todo.

## Progress Log

- 2026-08-04 (slot-9): filed after exhaustive live reproduction while blocked shipping
  `cve_affected_pinned_deps_remediation_2026_06_18.md`'s unified-trading-pm cryptography todo. Ruled out stale-cache,
  venv-contamination, and PM-specific-config explanations before concluding this is a genuine, fleet-wide
  `uv pip install -e` vs `[tool.uv] override-dependencies` visibility gap.
- 2026-08-04 (slot-12): closed todos #1 and #2. Re-enumerated LOCAL_DEPS fleet-wide (only 2 repos actually affected, not
  22). Empirically confirmed `--no-deps` breaks PM's own pydantic-dependent imports — rejected it and shipped a
  `--overrides <file>` fix instead (`unified-trading-pm@568cd6e17`), validated via genuine full `quality-gates.sh`
  passes (exit 0, sentinel==HEAD) on both affected repos (unified-trading-pm, deployment-service). Todo #3 remains open
  — genuinely operator-gated per its own text. Also filed
  `fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md` as an unrelated side-finding (this repo's
  own hygiene fixer strips the RULES.md-required `author` field from issue-doc frontmatter).

- **context-scout 2026-08-06**: re-scouted; `ci_local_qg_parity_2026_06_08.md` archived to `plans/archive/2026_06/`
  since first scouted, so its context_scope entry now points at the correct archived path (was a dead
  `plans/archive/2026_08/...` reference); otherwise re-verified context_scope (4 entries), unchanged.
