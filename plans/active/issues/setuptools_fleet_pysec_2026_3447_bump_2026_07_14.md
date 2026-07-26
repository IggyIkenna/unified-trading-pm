---
doc_type: issue
title:
  Fleet-wide setuptools 82.0.1 vulnerability (PYSEC-2026-3447) — pip-audit reddens the zero-tolerance codex gate on
  every repo pinning it; temporarily ignore-listed in e2e-testing, needs a proper fleet-wide bump to 83.0.0
summary:
  "Discovered 2026-07-14 while shipping an unrelated e2e-testing fix. pip-audit now flags setuptools 82.0.1 as
  PYSEC-2026-3447. setuptools 82.0.1 is installed fleet-wide (confirmed in e2e-testing and instruments-service venvs;
  market-tick-data-service also carries the PIP_AUDIT_EXTRA_ARGS allowlist pattern) and is a transitive dependency in
  the uv.lock files. Because it is NOT on any repo's pip-audit ignore-list, it fails the zero-tolerance codex-compliance
  gate (CODEX_MAX_VIOLATIONS=0) on every affected repo — blocking QG/shipping fleet-wide, not just for the commit that
  found it. Unlike the ~18 CVEs already on the allowlist (all marked 'no fix available'), a FIX EXISTS: setuptools
  83.0.0. Operator decision 2026-07-14: add PYSEC-2026-3447 to e2e-testing's allowlist NOW to unblock the in-flight defi
  reprobe fix, and file this issue for the proper fleet-wide bump (82.0.1 -> 83.0.0) as a separate task. The e2e-testing
  ignore is TEMPORARY and should be removed once the bump lands."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [setuptools, pip-audit, PYSEC-2026-3447, dependency, security, quality-gates, fleet-wide, ci-blocker]
related:
  [
    /plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-07-14
parent_epic: observability_master
priority: P2
source:
  Interactive session 2026-07-14 (slot-3·hk) — running e2e-testing QG for the defi reprobe read-path fix surfaced
  PYSEC-2026-3447 on setuptools 82.0.1 as the sole codex-gate violation.
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# Fleet-wide setuptools 82.0.1 vulnerability (PYSEC-2026-3447)

## What was found

While running `bash scripts/quality-gates.sh` in e2e-testing to gate an unrelated fix (the defi reprobe read-path
resilience change in `_dp_common.py`), the codex-compliance step failed with a single violation:

```
❌ pip-audit vulnerabilities found
  setuptools 82.0.1: PYSEC-2026-3447
❌ Codex compliance FAILED: 1 violations (max allowed: 0)
```

The change under test touches no dependencies, so the finding is diff-independent and pre-existing. setuptools 82.0.1 is
installed **fleet-wide**:

- `e2e-testing/.venv` → 82.0.1 (confirmed)
- `instruments-service/.venv` → 82.0.1 (confirmed)
- `market-tick-data-service` → carries the same `PIP_AUDIT_EXTRA_ARGS` allowlist pattern (very likely 82.0.1 too)
- transitive in the `uv.lock` files (pulled by another package, not a direct dependency)

Because PYSEC-2026-3447 is **not** on any repo's `--ignore-vuln` allowlist, it reddens the zero-tolerance
codex-compliance gate (`CODEX_MAX_VIOLATIONS=0`) on **every** affected repo — a fleet-wide QG/CI blocker, not a
single-commit problem.

## Why this is different from the existing allowlist entries

The ~18 CVEs already on e2e-testing's `PIP_AUDIT_EXTRA_ARGS` are all annotated "no fix available". **This one has a
fix**: `setuptools 83.0.0` (published 2026; supersedes the vulnerable 82.0.1). So the correct long-term remediation is a
**bump**, not an indefinite ignore.

## What was done now (temporary unblock)

Per operator decision 2026-07-14, `--ignore-vuln PYSEC-2026-3447` was added to `e2e-testing/scripts/quality-gates.sh`
`PIP_AUDIT_EXTRA_ARGS` (with a comment flagging it as temporary and pointing here) purely to unblock the defi reprobe
fix. This does **not** fix the vulnerability — it only silences the gate in one repo. instruments-service and MTDS
remain red on their next QG run until this issue is resolved.

## The proper fix (this issue)

Bump setuptools 82.0.1 → 83.0.0 across the affected repos:

1. Add a `setuptools>=83.0.0` constraint (or equivalent) so the transitive resolve picks the fixed version, then
   `uv lock` each affected repo (e2e-testing, instruments-service, market-tick-data-service, and any other repo whose
   lock pins 82.0.1 — sweep with a fleet grep).
2. Re-run each repo's `quality-gates.sh` to confirm pip-audit is clean without the ignore.
3. **Remove** the temporary `--ignore-vuln PYSEC-2026-3447` from `e2e-testing/scripts/quality-gates.sh` (and its
   comment) once the bump lands — the ignore must not outlive the fix.

## Acceptance

- No repo's `uv.lock` pins setuptools < 83.0.0.
- pip-audit is clean for PYSEC-2026-3447 fleet-wide with **no** `--ignore-vuln` entry for it.
- The temporary e2e-testing ignore + comment are removed.

## Todos

> Added 2026-07-26 by `/plan-reconcile` (infra shard). This doc was `status: open` with **zero checkboxes** —
> prose-only, so none of its work was visible to the hygiene/dispatch surface (the class
> `/plans/active/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md` todo 3 exists to sweep). No decision was invented:
> the todos below are the doc's own "The proper fix" 3 steps, with the current per-repo state MEASURED this turn so a
> worker starts from facts rather than the 2026-07-14 snapshot.
>
> **Measured 2026-07-26** (`grep -A1 '^name = "setuptools"' <repo>/uv.lock`): e2e-testing → **83.0.0** (already fixed);
> instruments-service → **82.0.1** (still vulnerable); market-tick-data-service → **82.0.1** (still vulnerable). And
> `grep -n PYSEC-2026-3447 e2e-testing/scripts/quality-gates.sh` → still present at **line 26** (`PIP_AUDIT_EXTRA_ARGS`)
> with its TEMPORARY comment at **line 36** — i.e. **the ignore has already outlived the fix in the one repo that is
> fixed**, which is precisely the failure mode this doc's Acceptance forbids ("the ignore must not outlive the fix").

- [ ] [SCRIPT] P2. Sweep every repo's `uv.lock` for a setuptools pin `< 83.0.0`
      (`grep -A1 '^name = "setuptools"' */uv.lock`), then for each hit add a `setuptools>=83.0.0` constraint (or
      equivalent) so the transitive resolve picks the fixed version and `uv lock` that repo. Known-affected as of
      2026-07-26: **instruments-service** (82.0.1) and **market-tick-data-service** (82.0.1); e2e-testing is already at
      83.0.0. **Done when**: the sweep command returns no version below 83.0.0 in any repo. Repo: per-repo (+
      unified-trading-pm if a canonical constraint is added).
- [ ] [SCRIPT] P2. Re-run each bumped repo's `bash scripts/quality-gates.sh` and confirm pip-audit is clean for
      PYSEC-2026-3447 **without** any `--ignore-vuln` entry for it. **Done when**: each touched repo's QG is green with
      the codex-compliance step reporting 0 violations. Repo: per-repo.
- [ ] [SCRIPT] P2. Remove the TEMPORARY `--ignore-vuln PYSEC-2026-3447` from `e2e-testing/scripts/quality-gates.sh`'s
      `PIP_AUDIT_EXTRA_ARGS` (line 26) **and** its explanatory comment (line 36). This one is already actionable on its
      own — e2e-testing's lock is at 83.0.0, so the ignore is currently masking nothing. **Done when**:
      `grep -n PYSEC-2026-3447 e2e-testing/scripts/quality-gates.sh` returns nothing and e2e-testing's QG is green.
      Repo: e2e-testing.
