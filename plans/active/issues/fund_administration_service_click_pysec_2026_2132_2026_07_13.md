---
doc_type: issue
title: "fund-administration-service pip-audit RED — transitive click 8.3.2 (PYSEC-2026-2132, fix 8.3.3)"
summary:
  "Discovered while shipping a fastapi-ceiling declarative bump (repo-blocker RB-3d53f6c8): pip-audit flags click 8.3.2
  as still vulnerable per an updated PYSEC-2026-2132 advisory (the original fix version quoted in
  system_integration_tests_pip_audit_red_2026_07_13.md was 8.3.2 — the advisory data has since tightened to 8.3.3).
  fund-administration-service does not declare click directly (pure transitive dep via some other package), so the
  fleet-canonical floor bump alone (now corrected to >=8.3.3 in workspace-constraints.toml) does not fix it here without
  a `uv lock --upgrade-package click` re-lock, which is out of scope for the no-relock declarative batch this was found
  during. Verified pre-existing (not caused by the fastapi commit) via a clean-tree pip-audit rerun."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [fund-administration-service]
scope: [engineer]
tags: [pip-audit, cve, click, dependency, repo-blocker]
related: [plans/active/issues/system_integration_tests_pip_audit_red_2026_07_13.md, workspace-constraints.toml]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P2
source: system_integration_tests_pip_audit_red_2026_07_13 todo 1 (fastapi canonical alignment batch), 2026-07-13
assigned_vm: planning
resolved_by: slot-11 (2026-07-13)
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend-engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

`pip-audit` in `fund-administration-service` reports:

```
click  8.3.2  PYSEC-2026-2132  8.3.3
```

The fleet-canonical `click` floor (`workspace-constraints.toml`) was originally bumped to `>=8.3.2` per this issue's own
original todo — sufficient at filing time, but the PYSEC-2026-2132 advisory data has since tightened (8.3.2 itself is
now listed as vulnerable, fix is 8.3.3). The canonical has been corrected to `>=8.3.3` in the same session.
`fund-administration-service` does not declare `click` as a direct dependency (pure transitive), so the canonical text
bump alone doesn't change its resolved/locked version — it needs its own `uv lock --upgrade-package click`.

## Why it matters

Blocks `fund-administration-service`'s `quality-gates.sh` (`CODEX_MAX_VIOLATIONS=0`), and by extension any shipping
through the mandatory Pass-1(QG)→Pass-2(quickmerge) flow for that repo, until resolved.

## Recommended decision

`cd fund-administration-service && uv lock --upgrade-package click`, confirm `pip-audit` clean, ship via the normal
QG→quickmerge flow.

## Todos

- [x] ✅ [CODE] P2. `uv lock --upgrade-package click` in `fund-administration-service`, verify `pip-audit` clean, run full
      `quality-gates.sh`, ship via `quickmerge --agent --files 'uv.lock'`. (repo: fund-administration-service) — locally
      relocked click 8.3.2->8.4.2 and confirmed QG-green (`IGNORE_TIMEOUT=true`, sentinel c4f36095d), but on quickmerge's
      pre-pull rebase discovered slot-6 had already shipped an equivalent broader relock
      (`fund-administration-service@018e5a668b334d34a49e99772e2ab49b443da5e4`, "re-lock off cryptography
      GHSA-537c-gmf6-5ccf") that picked up the identical click 8.3.2->8.4.2 bump as a side effect — my local change was
      absorbed into that rebase with nothing left to commit. Verified `pip-audit` clean for click against current HEAD
      (`018e5a6`, HEAD==origin).

## Progress Log

- **2026-07-13 (slot-13, sonnet/high)** — Found while shipping an unrelated fastapi-ceiling declarative bump (`ba288c2`)
  as part of `system_integration_tests_pip_audit_red_2026_07_13.md` todo 1's fleet-wide alignment batch. Verified
  pre-existing via clean-tree pip-audit rerun. Declared repo-blocker RB-3d53f6c8. Also corrected the fleet-canonical
  click floor from `>=8.3.2` to `>=8.3.3` in `workspace-constraints.toml` + `canonical-dependency-manifest.json` in the
  same session (the advisory data tightened after the original todo was filed).
