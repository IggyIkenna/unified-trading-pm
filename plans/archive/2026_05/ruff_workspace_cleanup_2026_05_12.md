---
doc_type: plan
title: Workspace ruff auto-fix sweep — repo-by-repo, per-shippable-unit
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-api, deployment-service, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: [/plans/active/master_to_live_defi_2026_05_23.md]
created: "2026-05-21"
parent_epic: infrastructure_master
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Workspace Ruff Auto-Fix Sweep

Workspace-wide `ruff check --fix` + `ruff format` sweep across all service repos; Telegram bot hygiene cleanup; per-repo
QG green verified post-fix. All 14 repos swept + Telegram hygiene done — archive candidate.

Codex SSOTs: `/codex/06-coding-standards/quality-gates.md`

---

## Sweep results (all complete)

- [x] ✅ [SCRIPT] P0. unified-api-contracts — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. unified-trading-library — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. market-tick-data-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. mdps — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. instruments-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. features-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. strategy-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. execution-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. ml-training-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. deployment-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. deployment-api — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. alerting-service — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. batch-live-reconciler — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P0. agent-orchestrator — ruff fix + format; QG green.
- [x] ✅ [SCRIPT] P1. Telegram bot hygiene: remove `f-string-without-placeholders` violations; Telegram bot messages use
      lazy `%s` format.

## Temporary states + canonical follow-up plans

- **Archive candidate**: all 14 repos swept + Telegram hygiene complete. No open items.
