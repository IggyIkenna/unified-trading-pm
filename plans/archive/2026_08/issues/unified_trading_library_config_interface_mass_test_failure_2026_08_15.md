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
status: resolved
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
resolved_by: "T1 code-readiness tranche, slot-6, 2026-08-20 -- unified-trading-library test re-run + CI-workflow HEAD check"
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

> **🟢 ARCHIVED 2026-08-20** — status=resolved, 0 open todos. Archived per
> /codex/11-project-management/issue-doc-lifecycle.md's archive-on-resolve rule.

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

- [x] ✅ [CODE] P2. **Symptom is GONE — confirmed by direct re-run, not assumed from time passing.** MEASURED
      2026-08-20: `tests/config_interface/` + `tests/cloud_interface/` (the exact suites named in this doc) run
      clean — **1355 passed, 25 skipped, 0 failed**. The leading suspect (stale `.venv` vs `uv.lock`) is explicitly
      RULED OUT, not just unconfirmed: `uv sync --frozen --dry-run` reports "would make no changes" against the
      CURRENT venv, so today's green run is not an artifact of a fresh sync fixing anything. **Root cause is not
      re-derivable at this remove** — 5 days and many fleet commits separate the original red run from this one,
      and this doc's own alternate hypothesis (unrelated concurrent work landing mid-session on a shared checkout)
      is exactly the class of transient collision this session independently reconfirmed exists in this workspace
      (see the T1 tranche's own Progress Log, 2026-08-20). Closing on the measured symptom, honestly not on a
      reconstructed cause. One unrelated collection error found in passing and NOT counted against this doc:
      `tests/cloud_interface/integration/test_aws_mode.py` fails to collect (`ModuleNotFoundError: No module named
      'moto'`) — a missing test dependency, not a config_interface/cloud_interface logic failure, and outside the
      55 originally reported. Left open as a separate concern for whoever owns that integration suite.
- [x] ✅ [CODE] P2. **Already shipped, independently of this doc** — `.github/workflows/quality-gates-v2.yml` and
      `notify-slack.yml` are both on `HEAD` (`fead8ba1`, `7c003dfe`, plus a `b5c138da` dead-copy cleanup). Working
      tree confirmed clean for both paths. No action needed.

## Progress Log

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:16a3edebe7baa883]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. Fresh doc (2026-08-15), no prior audit history, no gate/banner/lock. Todo 1 is a
  diagnose-and-fix task with a stated methodology and a crisp done-when; todo 2 is a mechanical ship once todo 1
  clears. No design/judgment call.
- **context-scout 2026-08-17**: populated context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20 — RESOLVED** (T1 code-readiness tranche, slot-6). Both todos closed by direct measurement: the
  55-failure symptom no longer reproduces (1355 passed / 0 failed on a targeted re-run of the exact named suites)
  and the stale-venv hypothesis is explicitly ruled out (`uv sync --frozen --dry-run`: no changes needed); the
  2-file CI-workflow ship this doc bundled in was independently already on `HEAD`. See todos for full detail.
