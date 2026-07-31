---
doc_type: issue
title: agent-orchestrator's quality-gates.sh never runs pip-audit at all
summary:
  "Discovered 2026-07-30 while re-auditing the fleet-wide QG_PIP_AUDIT_COMMON_IGNORES list
  (cve_affected_pinned_deps_remediation_2026_06_18.md). agent-orchestrator's scripts/quality-gates.sh deliberately does
  NOT source quality-gates-base/base-service.sh ('not a UTL-based trading service'), and has no equivalent pip-audit
  step of its own — so it never checks pip-audit at all, unlike every other Python repo in the fleet. CORRECTION (same
  day): an earlier version of this doc claimed 5 vulnerable packages (bleach/ecdsa/mistune/tornado/uv) found via a
  standalone `pip-audit` CLI check — that check was a methodology error (the standalone `pip-audit` on PATH resolves to
  a pyenv shim auditing an unrelated global/system Python environment, NOT the repo's actual `.venv`; confirmed those 5
  packages are not even installed in agent-orchestrator's `.venv`). The CORRECT check (`.venv/bin/python -m pip_audit`,
  matching base-service.sh's real invocation exactly) found ONE genuine finding: pyasn1 0.6.3
  (PYSEC-2026-3455/-3456/-3457, fix 0.6.4+) — already fixed fleet-wide as part of the same 2026-07-30 CVE remediation
  session (see Todos). The GATING gap (no pip-audit step at all in this repo's quality-gates.sh) remains real and open."
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [cve, pip-audit, agent-orchestrator, quality-gates, security]
related: [/plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md]
created: 2026-07-30
parent_epic: infrastructure_master
priority: P2
source:
  "2026-07-30 (slot-21) — surfaced while re-verifying the fleet-wide pip-audit ignore-list drop was safe; ran a
  standalone pip-audit against agent-orchestrator to sanity-check before shipping the empty QG_PIP_AUDIT_COMMON_IGNORES,
  and found its own quality-gates.sh never invokes pip-audit at all. The initial 5-package finding was corrected
  same-day after the operator asked for re-verification and the check was re-run correctly against the repo's own .venv."
assigned_vm: planning
resolved_by: agent-orchestrator@ec74605
locked_by:
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

> **✅ ARCHIVED 2026-07-31** — the sole todo (gate the standalone `agent-orchestrator/scripts/quality-gates.sh` on
> pip-audit) shipped `agent-orchestrator@ec74605` and was verified end-to-end (fresh run + cache-hit run, both green). 0
> open todos, unlocked. Moved to `plans/archive/issues/`.

# agent-orchestrator's quality-gates.sh never runs pip-audit

## What was found (corrected)

`agent-orchestrator/scripts/quality-gates.sh` carries this comment near the top: "UTL-based trading service, so it
deliberately does NOT source quality-gates-base/base-service.sh" — and has no equivalent pip-audit step anywhere in its
own ~56-line script. `grep -n "pip-audit\|pip_audit" scripts/quality-gates.sh` returns nothing.

**A methodology correction**: the check that first surfaced this doc used the standalone `pip-audit` binary on `$PATH`
(`/home/hk/.pyenv/shims/pip-audit`), which audits whatever Python environment that shim resolves to — NOT the repo's
actual `.venv`. That produced a false list of 5 "vulnerable" packages (bleach, ecdsa, mistune, tornado, uv) that turned
out not to even be installed in agent-orchestrator's `.venv`. The CORRECT check is `.venv/bin/python -m pip_audit`
(exactly what `base-service.sh`/`base-library.sh` invoke for every other repo) — re-run this way, it found exactly one
real finding: **pyasn1 0.6.3** (PYSEC-2026-3455, -3456, -3457; fix `pyasn1>=0.6.4`). This was confirmed also present
(and genuinely uncaught, sitting within an accepted per-repo codex-compliance violation-count tolerance rather than a
named `--ignore-vuln`) in 4 OTHER repos that DO run pip-audit: batch-live-reconciliation-service, execution-service,
market-data-processing-service, strategy-service. All 5 were bumped to pyasn1>=0.6.4 and shipped as part of the
2026-07-30 fleet CVE remediation (`cve_affected_pinned_deps_remediation_2026_06_18.md`).

## Why it matters

Every other Python repo in the fleet gates on pip-audit via `base-service.sh`/`base-library.sh`'s
`QG_PIP_AUDIT_COMMON_IGNORES` mechanism. agent-orchestrator is the one repo with a completely custom `quality-gates.sh`
and is silently exempt — not a deliberate security decision, just a gap in the custom script (it likely predates
pip-audit being wired into the shared base scripts, and was never backfilled). The pyasn1 finding above is direct proof
this gap has real consequences: a fleet-wide security audit needed a manual, out-of-band check to catch what should have
been caught by the repo's own gate.

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31.** Added a pip-audit step to `agent-orchestrator/scripts/quality-gates.sh` —
      sources `qg-common.sh` (the generic, repo-type-agnostic shared foundation, NOT `base-service.sh`'s UTL/UAC-
      specific enforcement) solely to reuse its cache/timeout/classify-by-output pip-audit pattern +
      `QG_PIP_AUDIT_COMMON_IGNORES` as the single fleet-wide ignore-list source of truth (never duplicated inline). Uses
      `.venv/bin/python -m pip_audit`, same graceful missing-PM-sibling fallback as the existing ENVIRONMENT block.
      Verified end-to-end: caught a genuinely stale local `.venv` (msgpack/pip/pyasn1/setuptools behind the
      already-fixed `uv.lock` pins) on the first run, clean after `uv sync`, cache-hits correctly on a second run.
      `bash scripts/quality-gates.sh` now runs pip-audit and the step is visible in its output (confirmed both the
      fresh-run and cache-hit paths). Shipped `agent-orchestrator@ec74605`. Repo: agent-orchestrator.

## Progress Log

- **na-eligibility-audit 2026-07-31**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-676f1e) —
  bounded/deterministic-outcome work (single script, one file, done-when is directly checkable), no operator gate or
  live judgment call found. Conflict-check run against every active `assigned_vm: planning` doc in
  `parent_epic: infrastructure_master` (incl. `cve_affected_pinned_deps_remediation_2026_06_18.md`, which
  cross-references this doc but only for its own prose-correction todo — already landed on this doc's current content,
  not a claim on the pip-audit-step implementation) + the infra tranche's consolidated-closeout digest: zero overlap,
  clear to proceed. Verified the underlying gap is still live today
  (`grep -n pip.audit agent-orchestrator/scripts/quality-gates.sh` — no match). Flipped `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`.
