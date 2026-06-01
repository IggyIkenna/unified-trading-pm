---
title: "Manifest consolidator liveness + health contract (heartbeat watchdog, loud-fail-default, preflight gate)"
created: 2026-06-01
status: active
parent_epic: manifest_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-06-01
---

# Manifest consolidator liveness + health contract

## What this fixes

The manifest consolidator is infrastructure that **must always run** (Cloud Run + Cloud Scheduler `*/1 * * * *`). When
it stops, today's failure mode is **silent**: a downstream reader's consolidated-index freshness check trips and the
reader **silently falls back to merging ALL per-VM shards** (~1700+ on cefi → ~12 GB pandas heap → SIGKILL). The
fallback masks a consolidator OUTAGE instead of surfacing it.

> Operator direction 2026-06-01: "we should never not have consolidator running, so I'm not sure we need a fallback —
> isn't the fix to loud-fail an event that manifest consolidation isn't running, or check a directory for consolidator
> events to ensure it's running, where consolidator can ping even if nothing to consolidate. Improve preflight manifest
> consolidator health."

This plan replaces the read-side fallback-as-default with a **consolidator liveness contract**.

## Grounding (verified 2026-06-01)

- **The consolidator already heartbeats every cycle, including no-op cycles**: `manifest_consolidator.py:290` emits
  `MANIFEST_CONSOLIDATED {no_op: True}` (nothing to consolidate) and `:341` emits `{no_op_unchanged: True}` (shards all
  already merged), and **both touch the canonical `_index/availability_index.parquet` mtime + stamp the
  `consolidator_run_at` GCS object-metadata marker**. So "fresh canonical mtime / recent run-at marker" already ==
  "consolidator ran this cycle"; in healthy operation the per-VM fallback should NEVER fire.
- **Gap 1**: nothing watches for the heartbeat's ABSENCE — `MANIFEST_CONSOLIDATED` has no liveness consumer.
- **Gap 2**: `MANIFEST_CONSOLIDATION_FAILED` is emitted on every failed cycle but is **consumed by NOTHING** (verified
  by workspace grep) → crash-looping consolidator is silent.
- **Gap 3**: the read-path fallback is silent-by-default (the opt-in fail-fast shipped in
  `manifest_reader_fail_fast_on_stale_fallback_2026_05_28` is the read-side enforcement, but it is opt-IN).

Models to reuse: `monitors/freshness_monitor.py::FreshnessMonitor.check_and_emit` (status + emit pattern);
`_resolve_fail_on_stale_fallback` / `ManifestConsolidatorStaleError` / `consolidator_run_at` marker
(`manifest_writer.py`).

## Provenance

- Extends `plans/active/manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md` (the opt-in read fail-fast → becomes
  the read-side enforcement of this contract).
- Composes with the per-group consolidation-health audit checks + `manifest_master_audit_instructions.md` (h2/h3/h4)
  added 2026-06-01.

## Implementation steps

- [x] ✅ [UTL] P1. UTL@3732ffaa — **Add event types** `CONSOLIDATOR_DOWN` (critical — heartbeat absent > N cycles) + `CONSOLIDATOR_STALE`
      (warn — a reader hit a stale/missing consolidated index) to `events/event_types.py` + re-export from
      `events/__init__.py`. Mirror the `DATA_STALE` / `FEED_UNHEALTHY` severity convention.
- [x] ✅ [UTL] P1. UTL@3732ffaa — **`assert_consolidator_healthy(bucket)` preflight helper** in `manifest_writer.py` (or
      `monitors/consolidator_liveness.py`): reads the consolidator heartbeat age (canonical mtime + `consolidator_run_at`
      marker, max-of), and raises `ManifestConsolidatorStaleError` + emits `CONSOLIDATOR_STALE` when age exceeds the
      staleness budget. Shared SSOT — the shell preflight (`deployment-service@7add531`) becomes a thin wrapper.
- [x] ✅ [UTL] P1. UTL@3732ffaa (guarded: only-when-other-VM-shards-exist + MANIFEST_ALLOW_STALE_FALLBACK opt-out + emit-not-silent; legacy opt-in retained) — **Promote read-path fail-fast opt-in → DEFAULT**: flip `_resolve_fail_on_stale_fallback` so a
      stale/missing consolidated index (when per-VM shards DO exist) RAISES `ManifestConsolidatorStaleError` + emits
      `CONSOLIDATOR_STALE` by **default**. The ~1700-shard per-VM merge becomes an explicit, opt-IN recovery escape-hatch
      via `MANIFEST_ALLOW_STALE_FALLBACK=true` (inverse of today). The genuinely-empty-bucket `_empty` path is
      unchanged. **Audit all 9 callers** in the read-fail-fast plan's Consumer-audit table before flipping; any caller
      that legitimately needs the recovery merge (e.g. a deliberate one-off reconcile) sets the opt-out.
- [x] ✅ [UTL] P1. UTL@3732ffaa — **Consolidator liveness watchdog** `monitors/consolidator_liveness.py::ConsolidatorLivenessMonitor`
      (modelled on `FreshnessMonitor`): per manifest bucket, reads last heartbeat age; emits `CONSOLIDATOR_DOWN`
      (critical) when a bucket misses > N cycles (default N=5 at `*/1`), recovery event when it returns. CLI entrypoint
      `python -m unified_trading_library.monitors.consolidator_liveness --buckets ...` for a Cloud Run Job.
- [x] ✅ [UTL] P1. UTL@3732ffaa (severity=ERROR) — **Wire `MANIFEST_CONSOLIDATION_FAILED` to alerting**: route it (and `CONSOLIDATOR_DOWN`) to the same
      alert sink as the existing `DATA_FRESHNESS_ALERT_ROUTED` path so a crash-looping consolidator pages.
- [x] ✅ [TEST] P1. UTL@3732ffaa — 141 tests green (13 (re-)written). Unit tests: heartbeat-fresh → healthy; heartbeat-stale → `CONSOLIDATOR_DOWN` + `assert_*` raises;
      recovery emits recovery; fail-fast default raises while opt-out merges; empty-bucket path unaffected.
- [ ] [INFRA] P2. **Deploy the watchdog**: Cloud Run Job + Cloud Scheduler (`*/2 * * * *`) per env, terraform in
      `deployment-service/terraform/gcp/`. Mirror the consolidator scheduler TF. (Runs-to-completion gate.)
- [x] ✅ [DOC] P2. codex@(this PR) — **Codex SSOT**: new "Liveness + health contract" section in
      `codex/05-infrastructure/manifest-consolidator-ssot.md` (heartbeat-every-cycle + watchdog + loud-fail-default +
      preflight gate) + cross-link from `codex/02-data/availability-manifest-and-data-status.md` § "Read path fail-fast".

## Success criteria

- C1: `CONSOLIDATOR_DOWN` + `CONSOLIDATOR_STALE` in UAC/UTL event registry; `assert_consolidator_healthy` exported.
- C2: read path raises (not silent-merges) by default on stale-with-shards; opt-out restores recovery merge; empty path
      unchanged. Unit tests green.
- C3: watchdog emits `CONSOLIDATOR_DOWN` on simulated heartbeat gap; `MANIFEST_CONSOLIDATION_FAILED` reaches the alert
      sink.
- C4: `bash scripts/quality-gates.sh` in `unified-trading-library` exits 0 for the touched files (composes with the
      pre-existing UTL QG-debt tracked in `issues/utl_full_qg_red_backlog_2026_06_01.md`).
- C5 (runs-to-completion): watchdog Cloud Run Job deployed + Scheduler enabled + one live cycle observed.

## Risks + mitigations

- **Risk**: flipping fail-fast to default breaks a batch/preflight caller that relied on the silent recovery merge.
  **Mitigation**: caller audit (9 known callers) before flip; `MANIFEST_ALLOW_STALE_FALLBACK=true` opt-out; emit
  `CONSOLIDATOR_STALE` so it's never silent either way.
- **Risk**: watchdog false-positives during a deploy window (brief consolidator gap). **Mitigation**: N=5 missed cycles
  default + recovery event; tune per bucket.
