---
doc_type: issue
title: agent-orchestrator's quality-gates.sh never runs pip-audit — 5 currently-vulnerable packages ungated
summary:
  "Discovered 2026-07-30 while re-auditing the fleet-wide QG_PIP_AUDIT_COMMON_IGNORES list
  (cve_affected_pinned_deps_remediation_2026_06_18.md). agent-orchestrator's scripts/quality-gates.sh deliberately does
  NOT source quality-gates-base/base-service.sh ('not a UTL-based trading service'), and has no equivalent pip-audit
  step of its own — so it never checks pip-audit at all. A direct `pip-audit --format json --skip-editable` run against
  agent-orchestrator's actual .venv found 36 known vulnerabilities across 5 packages, none covered by any ignore list
  because none was ever checked: bleach 6.3.0 (3 GHSA advisories), ecdsa 0.19.2 (PYSEC-2026-1325), mistune 3.2.0 (~13
  distinct PYSEC advisories), tornado 6.5.5 (3 PYSEC + 1 GHSA), and uv 0.10.8 itself (GHSA-pjjw-68hj-v9mw,
  GHSA-4gg8-gxpx-9rph — the same two IDs e2e-testing's own PIP_AUDIT_EXTRA_ARGS already ignores, confirming these are
  real/known, not a false positive). This is unrelated to the fleet-wide CVE bump work (agent-orchestrator was still
  bumped for setuptools/pip/msgpack/pydantic-settings/idna as part of that effort, on its own merits) — this doc is
  specifically about the GATING gap: nothing currently stops these 5 packages from drifting further, or a 6th appearing,
  because pip-audit never runs here."
status: open
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
  and found its own quality-gates.sh never invokes pip-audit at all."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# agent-orchestrator's quality-gates.sh never runs pip-audit

## What was found

`agent-orchestrator/scripts/quality-gates.sh` carries this comment near the top: "UTL-based trading service, so it
deliberately does NOT source quality-gates-base/base-service.sh" — and has no equivalent pip-audit step anywhere in its
own ~56-line script. `grep -n "pip-audit\|pip_audit" scripts/quality-gates.sh` returns nothing.

A direct check (`pip-audit --format json --skip-editable` against the repo's real `.venv`) found:

| Package | Version | Advisories                                                                        |
| ------- | ------- | --------------------------------------------------------------------------------- |
| bleach  | 6.3.0   | GHSA-g75f-g53v-794x, GHSA-gj48-438w-jh9v, GHSA-8rfp-98v4-mmr6                     |
| ecdsa   | 0.19.2  | PYSEC-2026-1325                                                                   |
| mistune | 3.2.0   | ~13 distinct PYSEC advisories (PYSEC-2026-2206 through -2218, -2651, -2652, -168) |
| tornado | 6.5.5   | PYSEC-2026-3387, -3388, -3389, GHSA-pw6j-qg29-8w7f                                |
| uv      | 0.10.8  | GHSA-pjjw-68hj-v9mw, GHSA-4gg8-gxpx-9rph                                          |

The `uv` findings are notable: these are the SAME two advisory IDs already present in e2e-testing's own
`PIP_AUDIT_EXTRA_ARGS` ignore list — confirming they are real, already-known findings elsewhere in the fleet, not a
false positive from this check. agent-orchestrator simply never surfaces them because nothing runs the query.

## Why it matters

Every other Python repo in the fleet gates on pip-audit via `base-service.sh`/`base-library.sh`'s
`QG_PIP_AUDIT_COMMON_IGNORES` mechanism (see `cve_affected_pinned_deps_remediation_2026_06_18.md` for the fleet-wide
state of that list, just re-audited and resolved 2026-07-30). agent-orchestrator is the one repo with a completely
custom `quality-gates.sh` and is silently exempt — not a deliberate security decision, just a gap in the custom script
(it likely predates pip-audit being wired into the shared base scripts, and was never backfilled).

## Recommended fix

Add a pip-audit step to `agent-orchestrator/scripts/quality-gates.sh`, ideally by sourcing the shared `qg-common.sh` for
its `QG_PIP_AUDIT_COMMON_IGNORES` constant (even though it can't source the full `base-service.sh`) so
agent-orchestrator doesn't maintain a third, divergent ignore list. Then evaluate each of the 5 currently-found
packages: bump if a fix version is compatible, or add a scoped `--ignore-vuln` with a documented reason (mirroring the
fleet convention) if genuinely blocked/disputed.

## Todos

- [ ] [SCRIPT] P2. **Add a pip-audit step to `agent-orchestrator/scripts/quality-gates.sh`.** Wire in
      `qg-common.sh::QG_PIP_AUDIT_COMMON_IGNORES` (now empty per the 2026-07-30 fleet re-audit) as the base ignore set,
      following the same cache/timeout/classify-by-output pattern `base-service.sh` uses (STEP documented there) rather
      than inventing a new one. **Done when**: `bash     scripts/quality-gates.sh` in agent-orchestrator runs pip-audit
      and the step is visible in its output. Repo: agent-orchestrator.
- [ ] [SCRIPT] P2. **Resolve the 5 currently-found vulnerable packages** (bleach, ecdsa, mistune, tornado, uv — see
      table above) once pip-audit is wired in: bump each to a fixed version where one exists and is compatible, or add a
      scoped `--ignore-vuln` with a one-line reason if genuinely blocked. **Done when**:
      `pip-audit --format json --skip-editable` against agent-orchestrator's `.venv` (or the wired-in QG step) shows
      zero unignored vulnerabilities. Repo: agent-orchestrator.
