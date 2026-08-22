---
doc_type: plan
title: Config-shard identity, idempotent force/freshness/skip for every service, and the DecisionTimeline + LatencyProfile for batch/paper/live
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 under the determinism-spine epic. Rulings D13 and D17
  (operator Q&A 2026-08-22) — every strategy / ML / execution result row and manifest row carries a deterministic,
  human-readable config-shard id with a short content-hash suffix, built from the axes that apply (client_id and
  slot_label for strategy, model_family / period / universe for ML, client_id / venue / region for execution, plus
  config version and code semver); a service checks the manifest for that id and skips unless --force, which re-runs as
  run_attempt+1. This supersedes the v7 "new job_id per re-run" manifest rule and adds code-semver + config-version
  columns (manifest v10). Observed pipeline timestamps (tick received → features ready → prediction → decision → order
  sent → ack → fill) are stored as facts in paper/live; in batch they are DERIVED at runtime from a LatencyProfile
  attached to the config shard (exchange→local delta where the source has it, 200 ms fallback, always widenable), so
  faster features/ML never rewrite TBs of history, and the profile hash lives in RunManifest so paper(W)==batch(W)
  stays ε=0.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy, backtest, paper, live, execution, meta]
repos: [unified-api-contracts, unified-trading-library, strategy-service, ml-service, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [config-shard, idempotency, force, skip-if-fresh, job-id, latency-profile, decision-timeline, run-manifest, semver, manifest-v10]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /plans/epics/batch_live_symmetry_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 9
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator Q&A 2026-08-22 (slot 6) — "human readable and short hash suffix ... check do i already have the id against manifest and skip ... unless --force then dump regardless"; "measured per venue where available, 200 ms fallback, always widenable"; "region matters ... testing higher delays is key to robustness"]
context_scope:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-trading-library/unified_trading_library/manifest_writer/_schema.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/config_versioning.py,
    unified-api-contracts/unified_api_contracts/external/tardis/schemas.py,
    strategy-service/strategy_service/engine/strategies/v2/base.py,
    strategy-service/strategy_service/portfolio_allocator/service.py,
    ml-service/ml_service/training/cli/handlers/final_training_handler.py,
    unified-trading-library/unified_trading_library/ml/model_registry.py,
    execution-service/execution_service/engine/backtest/node_builder.py,
  ]
---

# Config-shard identity + force/freshness/skip everywhere + DecisionTimeline / LatencyProfile

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md).
> Governing rulings: D13 (id + skip semantics), D17 (latency). The determinism spine
> (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) is the contract every change here must keep.

## Identity (D13)

`<human components>__cfg<config_version>__<code_semver>__<hash8>` where `hash8` = first 8 hex of
`sha256(canonical_config_repr(config) + code_semver + axes)` (reuse `ConfigDescriptor` / `canonical_config_repr` in UAC
`config_versioning.py`). Axes per service — strategy: `client_id`, `slot_label`; ML: `model_family`, `training_period`,
`universe`, `seed`; execution: `client_id`, `venue`, `region`. Within one (code semver, config version) the run is
idempotent: the service looks the id up in the manifest and skips; `--force` dumps regardless as `run_attempt+1` (audit
trail kept as attempts, not as new shards). The id is a column on every result row (ledger / prediction / fill) and the
manifest key, so results across configs are a `GROUP BY config_shard_id`.

## Timeline (D17)

Stored as facts everywhere: `period_end`, `available_at`, fill time, and — in paper/live only — the observed
`DecisionTimeline` (`tick_received_at`, `features_ready_at`, `prediction_at`, `decision_at`, `order_sent_at`, `ack_at`,
`fill_at`). In batch the timeline is derived at runtime from the config shard's `LatencyProfile`: inbound delay =
exchange→local delta where the source carries both (Tardis `timestamp` vs `local_timestamp`), else the profile's
per-venue / per-region assumed delay (200 ms total default, the nautilus `ImportableLatencyModelConfig` split 100 / 50
/ 50), plus a multiplier and offsets so robustness runs can widen it. Only `latency_profile_hash` is stored; it is part
of `RunManifest`.

## Todos

- [ ] [DESIGN] P0. **Supersede the v7 job_id rule** — amend `manifest_writer/_schema.py`'s v7 comment and
      `/codex/02-data/availability-manifest-and-data-status.md`: `job_id` = the D13 config-shard id; re-running the same
      (config version, code semver) is a skip unless `--force` (`run_attempt` column); manifest v10 adds
      `config_shard_id`, `config_version`, `code_semver`, `run_attempt`, `latency_profile_hash`. Done-when: codex + schema
      comment merged, v10 migration plan per `/codex/02-data/chunk-safe-manifest-migrations.md`.
- [ ] [BACKEND] P0. **UAC `ConfigShardId`** — builder + parser in `unified_api_contracts.canonical.crosscutting`
      (human components, `cfg<v>`, semver, `hash8` via `canonical_config_repr`), per-service axis sets, round-trip
      tests proving uniqueness (hash) and replayability (components). Done-when: shipped with guard tests.
- [ ] [BACKEND] P0. **Force / freshness / skip in strategy, ML, execution** — every batch CLI gains `--force`; the
      run pre-flight calls a UTL `check_config_shard_fresh(manifest, id)` (cell read, never a bare index read) and
      skips with a logged reason; `--force` writes `run_attempt+1`. Done-when: the three services show `--force` + the
      freshness call in their shard loops and a skip is proven on a re-run.
- [ ] [BACKEND] P0. **Code semver + config version on every row** — writers stamp `code_semver` (package version from
      the semver-agent tag) and `config_version` (`ConfigDescriptor`) on result rows + manifest rows; a QG check fails a
      writer that omits them. Done-when: one row per service shows both columns populated.
- [ ] [BACKEND] P0. **Config generated ahead of time and attached** — `RunManifest` snapshots the full config + its
      descriptor for the shard; `make-config-shards` CLI emits the id set for a grid (client × slot × config) so
      results can be compared across configs by id. Done-when: a grid of ≥ 3 configs produces 3 ids, 3 result sets,
      `GROUP BY config_shard_id` works.
- [ ] [DESIGN] P0. **`DecisionTimeline` + `LatencyProfile` contracts in UAC** — fields above; `LatencyProfile` keyed by
      (region, venue) with `assumed_total_ms` (200 default), `inbound_from_source: bool`, `multiplier`, `offset_ms`;
      `latency_profile_hash` in `RunManifest`. Done-when: contracts shipped; paper-batch-live codex § updated.
- [ ] [BACKEND] P1. **Batch derivation at runtime** — strategy + execution backtests compute sent/received from the
      profile (Tardis exchange→local where present) at run/read time; nothing derived is persisted; the nautilus
      latency model is built FROM the profile, not from ad-hoc venue dicts. Done-when: changing the profile changes the
      backtest fills with zero parquet rewrites.
- [ ] [BACKEND] P1. **Observed timeline in paper/live** — strategy / ML / execution stamp the `DecisionTimeline` on
      their STREAM_ONLY rows; `reconcile_day` reports live↔paper timeline deltas as execution alpha inputs. Done-when:
      one paper day shows all seven stamps.
- [ ] [DATA] P1. **Region as an execution config axis** — execution config shards carry `region`; the smoke matrix and
      cost model split execution results by region. Done-when: two regions produce two ids for the same client/venue.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo is
      `[x]`.

## Codex SSOTs

- `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — ε=0 spine; profile hash joins `RunManifest`.
- `/codex/04-architecture/ml-experiment-lifecycle.md` — ML job_id lifecycle; D13 id replaces the experiment-id form.
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest v10 columns + the superseded v7 rule.
- `/codex/02-data/chunk-safe-manifest-migrations.md` — how v10 lands without clobbering.

## Progress Log

- **2026-08-22 (operator Q&A, slot 6)**: Created from rulings D13 + D17.
