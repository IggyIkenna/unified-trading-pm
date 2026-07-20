---
doc_type: issue
title: >-
  UAC value-only registry/config edits break UTL's own tests with no gate able to see it — 2 instances within 24h
  (massive SOURCE_PRIORITY removal, SPORTS bucket key)
summary: >-
  A UAC edit that changes a registry VALUE (not a symbol) breaks a downstream consumer's own test suite while the
  consumer's tree never changes, so nothing re-runs its CI. Every existing gate is blind to it: SIT is an API-surface
  linter (static AST name-presence over sibling source; it installs only UAC and never runs a dependent's tests),
  detect_breaking_change.py is name-and-signature-only so a dict-value or YAML edit reads is_breaking=false, and
  cascade-qg-ordering.yml — the one component designed for this fan-out — dispatches `quality-gate-run`, an event NO
  repo declares a repository_dispatch listener for, so it fails GREEN by reading the pre-existing ci_status. Instance 1
  (uac@a2beed46, massive removed from SOURCE_PRIORITY) reddened UTL main for ~9h undetected and was then laundered green
  by SIT. Instance 2 (uac@1ff91e5b, SPORTS key dropped from cloud-providers.yaml) is LATENT — it breaks
  test_bucket_naming_cell_sweep locally against UAC-LDR but has not reached UAC main yet.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-repo, ci-cd, sit, breaking-detection, data-correctness, quality-gates]
related:
  [betfair_instrument_id_delimiter_cross_repo_2026_07_08.md, tradfi_canonical_path_migration_design_2026_07_19.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-07-20 while root-causing the overnight T0 FAILURE + CI REGRESSION alerts on unified-trading-library",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
---

# UAC value-only config changes break UTL with no gate able to see it

## The class

An upstream T0 (UAC) changes a **value** inside a registry or config file. A downstream T0/T1 consumer's behaviour is
derived from that value at runtime, so the consumer's own tests break — but the consumer's tree never changed, so its CI
never re-runs and nothing notices.

## Instances (all authored by UAC within 24h of each other)

| #   | UAC commit | Change                                           | Downstream effect                                                          | State                        |
| --- | ---------- | ------------------------------------------------ | -------------------------------------------------------------------------- | ---------------------------- |
| 1   | `a2beed46` | `massive` removed from tradfi `SOURCE_PRIORITY`  | 10 UTL manifest-writer tests fail                                          | FIXED (fixtures repointed)   |
| 2   | `1ff91e5b` | `SPORTS` key dropped from `cloud-providers.yaml` | 2 `test_bucket_naming_cell_sweep` cells fail (`gcp`/`aws:features:sports`) | **OPEN — latent, see below** |

Instance 1 timeline: UTL v2 green 07-19 17:22Z → UAC `a2beed46` lands 17:34Z → overnight audit 07-20 02:20Z finds 10
failures. UTL main was red for ~9h with nothing detecting it, then SIT stamped `SIT_VALIDATED` at 05:21Z and erased the
red entirely (that laundering is separately fixed — see `ci_status_store.resolve_status`'s main-red provenance guard).

## Instance 2 — the open one

`resolve_bucket_name(cloud='gcp', kind='features', asset_group='sports')` raises
`BucketNamingError: Kind 'features' on cloud 'gcp' has no entry for asset_group='sports'. Available: ['CEFI', 'DEFI', 'PREDICTION', 'TRADFI']`.

Priority-setting facts measured 2026-07-20:

- `1ff91e5b` is **NOT on UAC main** (LDR only) — so this has not reddened UTL main yet.
- The sweep **did not run at all** in the 02:20Z CI slice (0 occurrences in that run's log), so CI has not seen it.
- It **does** reproduce locally against the sibling UAC-LDR checkout.

So it fires when the UAC SPORTS removal promotes to main, not before.

### The actual defect is a discovery-precedence mismatch, not a stale fixture

`test_bucket_naming_cell_sweep._build_sweep_params()` (`tests/cloud_interface/unit/`) is correctly written to derive its
cells from the live YAML rather than hardcoding them — it iterates `_load_cloud_providers_yaml()` and keeps only keys in
`_ASSET_GROUPS`. But **collection-time and run-time resolve different files**:

- at collection the loader yields a mapping that still contains `SPORTS` (hence the `gcp:features:sports` param exists)
- at run time, with the autouse `_reset_yaml_cache` fixture applied, it resolves UAC's
  `unified_api_contracts/config/cloud-providers.yaml`, whose `features` entry is `['CEFI','TRADFI','DEFI','PREDICTION']`

`unified-trading-library/tests/fixtures/cloud-providers.yaml` still carries `SPORTS` at lines 66 / 202 (and for
`market-data-tick` / `instruments-store`), which is the likely collection-time source. **Do not just delete those
lines** — first establish which YAML the sweep is supposed to be authoritative against, because a fixture that silently
shadows the real config at collection but not at execution will keep producing phantom cells for every future key
change.

## Why no gate catches the class

1. **SIT is an API-surface linter, not an integration test.** `full-workspace-sit.yml` installs only UAC
   (`uv pip install -e unified-api-contracts pytest pyyaml`) and runs one step: `run_cross_repo_invariants.sh`. UTL is
   cloned but never installed, never imported, and its `tests/` are never collected. The UTL invariant AST-parses
   `unified_trading_library/__init__.py` and asserts 27 symbol names still exist. `SOURCE_PRIORITY` still exists and is
   still exported — only its value changed. So `SIT_VALIDATED` means "the names other repos import still exist", not
   "the resolved combination works".
2. **The differ is value-blind.** `detect_breaking_change.py` compares export sets, signatures, class fields and routes.
   Its own docstring: _"NOT breaking: … body changes."_ `SOURCE_PRIORITY` is an `AnnAssign` whose dict value changed;
   `cloud-providers.yaml` is not Python at all. Verdict `false` either way — and every downstream gate
   (`breaking_pending`, `tier_c_promotion_gate`, the cascade trigger) keys off that same verdict.
3. **The reverse-dependency fan-out fails green.** `cascade-qg-ordering.yml` builds a reverse dep graph and dispatches
   `quality-gate-run` to each dependent — which would run UTL's suite. But `quality-gate-run` appears in exactly one
   file workspace-wide: the emitter itself. No repo declares a `repository_dispatch` listener for it (UTL's v2 accepts
   only `push:[main]`, `pull_request:[main,staging]`, `workflow_dispatch`). The dispatch 204s, nothing runs, and
   `poll_level` then reads the _pre-existing_ `ci_status` — already `MAIN_GREEN`/`SIT_VALIDATED`, both in
   `PASSING_STATUSES` — and declares the level green. This is a false-green by construction, not merely a miss.
4. **A red SIT never reaches an agent.** `full-workspace-sit.yml` dispatches only `sit-passed`/`sit-failed`;
   `sit-unlock.yml` opens a GitHub Issue + Slack. The one auto-escalation for repeated SIT failure sends
   `wall_type: "sit_retry_cap"`, which is not in `escalate-to-orchestrator.yml`'s accepted set, so it hard-errors.

## Todos

- [ ] [DEVOPS] P0. Establish which `cloud-providers.yaml` the bucket-naming sweep is authoritative against, fix the
      collection-vs-runtime precedence mismatch, and make instance 2 green — do NOT just delete the fixture's `SPORTS`
      lines without resolving precedence first.
- [ ] [DEVOPS] P0. Add a `repository_dispatch: types: [quality-gate-run]` listener to consumer `quality-gates-v2.yml` so
      `cascade-qg-ordering.yml`'s fan-out actually lands, and make `poll_level` distinguish "the dependent really
      re-ran" from "a stale ci_status was already green" (the current false-green is dangerous independently of the
      trigger).
- [ ] [DEVOPS] P1. Make `detect_breaking_change.py` value-aware for registry constants: hash the VALUES of the known
      cross-repo registries (`SOURCE_PRIORITY` and peers) plus the config YAMLs UAC ships, so a value-only edit sets
      `is_breaking` and the cascade fires.
- [ ] [DEVOPS] P2. Fix the invalid `sit_retry_cap` wall_type in `sit-debounce-trigger.yml` (it can never succeed) and
      decide whether a red SIT should escalate to a background worker rather than Issue + Slack only.
- [ ] [DEVOPS] P2. Correct the `full-workspace-sit` messaging/naming so `SIT_VALIDATED` cannot be read as "the resolved
      cross-repo combination was executed" — it is a surface check.

## Progress Log

- **2026-07-20** — Class identified while root-causing the overnight T0 alerts. Instance 1 fixed (UTL fixtures repointed
  onto still-multi-source cells; `(tradfi, ohlcv_15m)` remains `["databento","yahoo"]` while `trades` collapsed to
  single-source). The SIT-laundering half is fixed separately in `ci_status_store.resolve_status`. Instance 2 diagnosed
  to a collection-vs-runtime YAML precedence mismatch and left open — deliberately not band-aided.
