---
doc_type: issue
title:
  CLI shard-split flag coverage audit — the codex 6-tuple/--shard-key convention is real in only 1 of 4 sampled services
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §9 found the codex 6-tuple (day, chain, league, fixture,
  instrument_type + `--shard-key`) convention is REAL in exactly one of 4 sampled services (market-tick-data-service,
  the reference implementation — `decompose_shard_key` has zero hits in instruments-service, MDPS, or features-service)
  and ASPIRATIONAL elsewhere. instruments-service's `--operation download` entrypoint has no
  `--shard-key`/`--instrument-type`/`--day`/`--root` at all. Two audit asks tracked here.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, market-data-processing-service, features-service]
scope: [engineer, admin]
tags: [cli-convention, shard-key, cli-flags, instruments-service, mdps, features-service]
related: [/codex/06-coding-standards/cli-convention.md, /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §9
depends_on: []
---

# CLI shard-split flag coverage audit

## Todos

- [ ] [BACKEND] P1. Audit CLI shard-split flag coverage across instruments-service, market-data-processing-service, and
      every features-service family CLI against the codex 6-tuple (day, chain, league, fixture, instrument_type) +
      `--shard-key` convention (`/codex/06-coding-standards/cli-convention.md`). Definition-of-done: a per-service gap
      list (which flags exist, which are missing) — starting from the known baseline that `market-tick-data-service` is
      the only reference implementation and `instruments-service`'s `--operation     download` entrypoint has none of
      `--shard-key`/`--instrument-type`/`--day`/`--root`.
- [ ] [BACKEND] P2. Enumerate every chain-scoping CLI flag on instruments-service's download entrypoint (baseline found:
      `--gas-fee-chains`, `--evm-defi-chains`, `--lending-chains`, `--risk-params-chains`) and confirm whether
      features-service's onchain family CLI accepts the same set. Definition-of-done: a stated yes/no per flag, with a
      gap filed for each missing one.
