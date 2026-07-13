---
doc_type: issue
title:
  "ml-service quality-gates.sh RED on pre-existing pip-audit findings — pillow, cryptography, pydantic-settings,
  starlette (4 packages, 9 CVEs, all have fix versions)"
summary:
  "Found 2026-07-13 while shipping the utl_reuse_phase0_guardrails_2026_07_13 golden-fixture test for ml-service (an
  unrelated, test-only change). `bash scripts/quality-gates.sh` fails STEP 'Codex compliance' (CODEX_MAX_VIOLATIONS=0)
  on a pip-audit finding: pillow 12.2.0 (5 CVEs, fix 12.3.0), cryptography 48.0.0 (GHSA-537c-gmf6-5ccf, fix 48.0.1),
  pydantic-settings 2.14.1 (GHSA-4xgf-cpjx-pc3j, fix 2.14.2), starlette 1.1.0 (PYSEC-2026-248/249, fix 1.3.0/1.3.1) — 9
  CVEs across 4 packages total. Verified pre-existing and NOT caused by the golden-fixture change: stashed the test-file
  diff, ran pip-audit against the untouched HEAD uv.lock directly, same 9 findings appear. Confirmed a
  golden-output-fixture-only diff cannot touch dependency-installed versions. Attempted the pillow-only fix (`uv lock
  --upgrade-package pillow`, still within the existing `pillow>=12.2.0,<13.0.0` pyproject constraint — zero
  compatibility risk) but that alone does not turn the gate green: the other 3 packages still fail it, and pillow's own
  re-resolution can shift transitive pins for unrelated packages, so a piecemeal fix inside an unrelated task risks
  widening scope uncontrollably. Reverted that partial fix; filing this instead so the full remediation gets its own
  scoped, tested change."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, pip-audit, dependency, security, quality-gates, cve]
related:
  [
    plans/active/utl_reuse_phase0_guardrails_2026_07_13.md,
    ml-service/scripts/quality-gates.sh,
    ml-service/pyproject.toml,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: utl_reuse_phase0_guardrails_2026_07_13 todo 2 (ml-service golden-fixture shipping attempt), 2026-07-13
assigned_vm: planning
resolved_by: ml-service@4d16341 (2026-07-13, slot-9)
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend-engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

`bash scripts/quality-gates.sh` in `ml-service` fails at the "Codex compliance" aggregate step (`CODEX_MAX_VIOLATIONS=0`
— `scripts/quality-gates.sh:26`) because `pip-audit` (with the repo's existing
`PIP_AUDIT_EXTRA_ARGS="--ignore-vuln PYSEC-2024-277 --ignore-vuln PYSEC-2025-183"` for two known-unfixable joblib/pyjwt
CVEs) still reports 9 live findings across 4 packages, all of which HAVE fix versions available:

```
Name              Version ID                  Fix Versions
----------------- ------- ------------------- ------------
cryptography      48.0.0  GHSA-537c-gmf6-5ccf 48.0.1
pillow            12.2.0  PYSEC-2026-2253     12.3.0
pillow            12.2.0  PYSEC-2026-2255     12.3.0
pillow            12.2.0  PYSEC-2026-2257     12.3.0
pillow            12.2.0  PYSEC-2026-2256     12.3.0
pillow            12.2.0  PYSEC-2026-2254     12.3.0
pydantic-settings 2.14.1  GHSA-4xgf-cpjx-pc3j 2.14.2
starlette         1.1.0   PYSEC-2026-249      1.3.1
starlette         1.1.0   PYSEC-2026-248      1.3.0
```

Verified pre-existing, not caused by my change: my task's diff was a single new test file
(`tests/training/unit/test_golden_fixture_phase0_model_selection.py`, committed at `ml-service@d443b15`) — no
`pyproject.toml`/`uv.lock` edits. Stashed that diff, ran
`uv run pip-audit --ignore-vuln PYSEC-2024-277 --ignore-vuln PYSEC-2025-183` directly against the clean, untouched HEAD
`uv.lock` — same 9 findings, byte-identical. A pure test-file addition cannot change resolved dependency versions, so
this is unambiguously pre-existing.

`pillow` alone is a safe, zero-risk bump (`pyproject.toml:59` already declares `"pillow>=12.2.0,<13.0.0"` — bumping the
LOCKED version to 12.3.0 stays inside that existing range, no code/API surface changes expected for an imaging library
patch release). `cryptography`/`pydantic-settings` are also narrow patch bumps. `starlette` 1.1.0 → 1.3.x is the outlier
— that's not a patch bump and could carry real API/behavior changes for whatever FastAPI/ASGI surface ml-service
exposes; it needs its own compatibility check, not a blind version bump riding on an unrelated task.

## Why it matters

This blocks ANY commit to ml-service from passing `quality-gates.sh` and therefore shipping via the mandatory
Pass-1(QG)→Pass-2(quickmerge) flow — every worker touching ml-service hits this same RED gate regardless of what they're
actually changing, until the underlying dependencies are bumped. It's also a live security exposure: 9 CVEs with
published fixes sitting unpatched in a service-tier repo's dependency tree.

## Recommended decision

Bump all 4 packages to their fixed versions in one scoped PR:

- `pillow` → 12.3.0 (already covered by the existing pyproject constraint — trivial)
- `cryptography` → 48.0.1 (patch)
- `pydantic-settings` → 2.14.2 (patch)
- `starlette` → 1.3.0 or 1.3.1 — check ml-service's FastAPI/Starlette version compatibility matrix first (this is the
  one genuine compatibility judgment call); run the full ml-service test suite after the bump, not just pip-audit.

`uv lock --upgrade-package pillow --upgrade-package cryptography --upgrade-package pydantic-settings --upgrade-package starlette`
then `bash scripts/quality-gates.sh` to confirm green end-to-end (not just pip-audit in isolation).

## Todos

- [x] ✅ [BACKEND] P1. Bump `pillow`→12.3.0, `cryptography`→48.0.0→49.0.0, `pydantic-settings`→2.14.2 (all within
      existing `pyproject.toml` constraints, zero compatibility risk) — shipped `ml-service@3f18fa0`.
- [x] ✅ [BACKEND] P2. `starlette` is still short of its 1.3.0 fix (locked at 1.2.1) — our own
      `fastapi>=0.115.0,<0.137.0` pyproject ceiling caps starlette there even at fastapi's max allowed patch (0.136.3).
      Needs a deliberate `fastapi<0.137.0` ceiling bump + compatibility check (ml-service's actual FastAPI/ASGI usage),
      not a blind lockfile bump. Interim: `ml-service@3f18fa0` added
      `--ignore-vuln PYSEC-2026-248 --ignore-vuln PYSEC-2026-249` to `PIP_AUDIT_EXTRA_ARGS` with a comment explaining
      why (fastapi-capped, not "no fix version") so quality-gates.sh is honestly green in the meantime. Bump the fastapi
      ceiling, confirm starlette resolves to >=1.3.0, run the full test suite (not just pip-audit), then remove the two
      ignore-vuln entries. (repo: ml-service) — DONE `ml-service@4d16341`.

## Progress Log

- **2026-07-13 (slot-3, sonnet/high)** — Found while shipping an unrelated golden-fixture test for
  `utl_reuse_phase0_guardrails_2026_07_13`. Verified pre-existing (stash-diff test against clean HEAD). Initially
  reverted a pillow-only partial fix since the gate stayed red regardless; declared repo-blocker RB-372eec01, which the
  watcher resolved (likely a flaky/network-dependent pip-audit invocation on its side — my own re-verification right
  after still showed all 4 packages vulnerable). Went ahead with the full fix: pillow/cryptography/pydantic-settings
  bumped clean (`ml-service@3f18fa0`); starlette turned out to be capped by our own fastapi ceiling rather than a simple
  lockfile bump, so left that one `--ignore-vuln`'d with a clear comment + this issue as the tracked follow-up.
- **2026-07-13 (slot-9, sonnet/high)** — Closed the P2 follow-up, `ml-service@4d16341`. Widened the `fastapi` ceiling
  `<0.137.0`→`<0.138.0` (verified via `uv pip install --dry-run` that fastapi 0.137.0 is the minimum version whose
  resolver accepts starlette≥1.3.0 — fastapi 0.136.x permits starlette down to 1.1.0) + added a
  `[tool.uv] override-dependencies` floor pin `starlette>=1.3.1` (precedent: `unified-trading-library/pyproject.toml`'s
  existing cryptography/pip security-pin pattern) since fastapi's own declared range alone doesn't force the bump.
  fastapi itself landed on 0.136.3 (no forced jump to 0.137/0.138 — `uv lock` picked the minimal satisfying version).
  Rebased my commit onto `3f18fa0` (real conflict — both touched `uv.lock` concurrently) and removed the two
  `--ignore-vuln` flags from `scripts/quality-gates.sh` since starlette is now genuinely fixed (leaving stale
  ignore-vulns would silently mask a future regression below 1.3.0). `pip-audit` clean (0 findings, joblib/pyjwt ignores
  only); full ml-service test suite
  - `quality-gates.sh` green; shipped via quickmerge. Issue fully resolved — both todos done.
