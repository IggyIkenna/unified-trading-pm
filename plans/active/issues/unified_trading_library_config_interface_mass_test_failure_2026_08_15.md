---
doc_type: issue
title:
  "unified-trading-library: 55 test failures in config_interface/cloud_interface, unrelated to any known in-flight
  change"
summary: >-
  A full quality-gates.sh run on 2026-08-15 found 55 failing tests in unified-trading-library — entirely in
  config_interface (GCS config loaders, TimeSeriesConfigStore persistence, removed-methods) and cloud_interface
  (region-default constants) — none of which the discovering session touched. Cause not yet root-caused; the gate's own
  pre-flight warned the local .venv was stale against uv.lock, which is the leading suspect but is unconfirmed.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [test-failure, config-interface, cloud-interface, ci, unified-trading-library]
related: []
created: 2026-08-15
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P2
source:
  "Discovered auditing an unrelated 2-file CI-workflow ship (.github/workflows/quality-gates-v2.yml + a new
  notify-slack.yml) that needed unified-trading-library's own quality-gates.sh green before it could ship."
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: default
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
last_updated:
supersedes:
superseded_by:
depends_on:
assigned_role: infra
effort: medium
drift_direction:
locked_since:
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    unified-trading-library/tests/config_interface/,
    unified-trading-library/tests/cloud_interface/,
    unified-trading-library/.github/workflows/quality-gates-v2.yml,
  ]
---

## Finding

`cd unified-trading-library && bash scripts/quality-gates.sh --no-fix` (2026-08-15, ~504s pytest runtime) reported **55
failed, 7015 passed, 11 skipped, 10 xfailed**. Every failure is in one of:

- `tests/config_interface/unit/test_loaders_gcs.py` (GCS config loading)
- `tests/config_interface/unit/test_persistence.py` (`TimeSeriesConfigStore` replay-at / config-for-date / save-load — a
  large cluster, ~7 tests)
- `tests/config_interface/unit/test_removed_methods.py` (`BaseConfig.get_secret`/`validate_cloud_resources`
  expected-raise tests)
- `tests/config_interface/integration/test_library_deps_integration.py`,
  `tests/config_interface/integration/test_unified_cloud_config.py` (project-id/GCS-region defaults)
- `tests/cloud_interface/unit/test_constants.py::test_get_region_gcp_default`

The discovering session's own change was two `.github/workflows/*.yml` files (a self-hosted-runner migration + a new
`notify-slack.yml` reusable workflow) — nothing in `config_interface`/`cloud_interface`. Not root-caused: the gate's own
pre-flight printed
`⚠ WARN — .venv is STALE against uv.lock ... A stale venv can stop the suite COLLECTING, so treat a red pytest here as possibly environmental`
— plausible (a config-loading/defaults cluster failing wholesale smells like a stale dependency or a changed default
picked up by a re-synced env, not 55 independent logic bugs), but this was NOT verified by re-running after a clean
`uv sync`. Could also be genuine breakage from unrelated concurrent work landing on this branch (the workspace's shared
multi-agent checkouts made this exact class of surprise common throughout the same session — see the sibling session's
parallel discovery of a stray `git stash`-conflict in `agent-orchestrator/server/model_pricing.py` from unrelated
concurrent DeepSeek/GLM pricing work).

## Why this wasn't fixed in the discovering session

Context ran out mid-session (pre-compact checkpoint triggered at ~65% usage) while several other repos' shipping was
still in flight; investigating 55 failures across two modules was out of scope for what was already a very large
session. The 2-file CI-workflow change this session was trying to ship is unrelated in content and was left uncommitted
rather than force-shipped past a red gate.

## Todos

- [ ] [CODE] P2. **Root-cause the 55 config_interface/cloud_interface failures.** Start with `uv sync --frozen` on a
      fresh clone (or `rm -rf .venv && uv sync`) and re-run `bash scripts/quality-gates.sh --no-fix` to rule out the
      stale-venv hypothesis first — cheapest check, matches the gate's own warning. If still red after a clean sync,
      diagnose for real: `TimeSeriesConfigStore` persistence + GCS loader failures together suggest either a changed GCS
      client/library default, a changed `UnifiedCloudConfig` default (`project_id`/`gcs_region`), or a fixture/mock
      drift — read the actual failure output (`pytest tests/config_interface -x` via `quality-gates.sh`, never raw
      `pytest`) rather than guessing from test names. Done-when: `bash scripts/quality-gates.sh` green on
      `unified-trading-library`.
- [ ] [CODE] P2. **Ship the 2-file CI-workflow change** (`.github/workflows/quality-gates-v2.yml` self-hosted-runner
      migration + billing-kill gate + `ci_trigger_branch` support for `ldr_terminal` repos, and the new
      `.github/workflows/notify-slack.yml` reusable Slack-notification carrier) once the above is green — this was
      reviewed as safe/complete this session (self-consistent diff, references the same `ldr_terminal` concept this
      session independently confirmed for `agent-orchestrator`) but was never shipped because the full-repo gate
      couldn't go green for the unrelated reason above. Ship via
      `bash scripts/quickmerge.sh "<message>" --agent --files '.github/workflows/quality-gates-v2.yml .github/workflows/notify-slack.yml'`.

## Progress Log

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:16a3edebe7baa883]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. Fresh doc (2026-08-15), no prior audit history, no gate/banner/lock. Todo 1 is a
  diagnose-and-fix task with a stated methodology and a crisp done-when; todo 2 is a mechanical ship once todo 1
  clears. No design/judgment call.
- **context-scout 2026-08-17**: populated context_scope (4 entries).
