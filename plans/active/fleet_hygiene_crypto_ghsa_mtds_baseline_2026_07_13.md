---
doc_type: plan
title: Fleet Hygiene — cryptography GHSA floor bump + MTDS QG baseline ratchet-down
summary:
  Bump the fleet's cryptography dependency off the GHSA-537c-gmf6-5ccf advisory line and drop the transient
  --ignore-vuln; ratchet MTDS's DTZ + fallback-import QG baselines down now that the underlying fix already landed.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [dependency, security, quality-gates, hygiene, fleet-wide]
related: [v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up 2026-07-13]
sequential: false
---

# Fleet Hygiene — cryptography GHSA bump + MTDS baseline ratchet

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md)
> Follow-ups section — both items are mechanical, unblocked, and unrelated to the strategy-engine work in the parent
> plan; grouped here as one small hygiene sweep rather than two separate micro-plans.

## Ground truth (2026-07-13 verification — do not re-derive)

- The `GHSA-537c-gmf6-5ccf` ignore for `cryptography` 46.0.7 (statically-linked OpenSSL) is confirmed still present in
  `unified-trading-pm/scripts/quality-gates-base/base-service.sh:1307-1310` and `base-library.sh:946+`, both explicitly
  cross-referencing this plan's parent by name. It is a transient speed>security unblock, not the fix.
- MTDS is confirmed below both `ruff_rule_ratchet_baseline.yaml` (32) and `no_fallback_imports_baseline.yaml` (3) after
  the DTZ noqa fix already shipped — the ratchet-down just hasn't been run.

## Todos

- [ ] [SCRIPT] P2. Bump the `cryptography` dependency floor fleet-wide (every repo declaring it, directly or
      transitively) to a version outside the `GHSA-537c-gmf6-5ccf` line; regenerate `uv.lock` per repo. Repo:
      fleet-wide.
- [ ] [SCRIPT] P2. Remove the `GHSA-537c-gmf6-5ccf` `--ignore-vuln` from both
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh` and `base-library.sh` once the bump above is
      confirmed green across the fleet — do not remove the ignore before every dependent repo's QG has actually passed
      with the new floor. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. Ratchet DOWN `ruff_rule_ratchet_baseline.yaml` and `no_fallback_imports_baseline.yaml` for
      market-tick-data-service by re-running `--update-baseline` — baselines only go DOWN, never up, per the
      coding-standards HARD RULE. Repo: unified-trading-pm.

## Progress Log

(loop handoff lands here)
