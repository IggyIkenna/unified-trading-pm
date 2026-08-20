---
doc_type: issue
title: >-
  `MANIFEST_ALLOW_STALE_FALLBACK=true` silently returns a badly-incomplete manifest view when the consolidator has been
  down/paused a LONG time — a caller can run to a clean "done" having processed <2% of real work
summary: >-
  `unified_trading_library.manifest_writer._read_index._read_slow_path`'s `MANIFEST_ALLOW_STALE_FALLBACK=true` escape
  hatch for `ManifestConsolidatorStaleError` is memory-safe for a filtered caller (`filters=` bounds decode cost via
  row-group pushdown — confirmed correct), but is NOT data-complete for a consolidator that has been down/paused for a
  long stretch. The recovery merge (`_read_and_merge_per_vm_shards`) reconstructs its view ENTIRELY from
  currently-existing `_index/per_vm/*` shard files — it never reads the stale consolidated blob's own content at all.
  Per-VM shards get PRUNED after each successful consolidation cycle (`manifest_consolidator.py`'s post-merge prune —
  "after a successful canonical write we prune shards whose rows are DEFINITELY already in [the consolidated index]").
  So once a consolidator has been paused long enough that everything written BEFORE the pause has already been pruned,
  the stale-fallback view only shows whatever ACTIVE writers have written SINCE the pause began — missing essentially
  all historical data. Confirmed live 2026-08-07: with the DeFi consolidator paused ~16h for an unrelated session's
  `canonical-migration-defi-rebuild` VM, using this flag to unblock the dex_swaps legacy-fold script made its worklist
  look like 260 shards instead of the real ~27,549 (46,263 captured rows across 4 venues, vs the real ~3.46M rows across
  22 venues measured earlier the same session when the consolidator was fresh). The script ran to completion, logged
  zero errors, and reported a clean `done (apply=True)` totals line — a textbook false-completion signature: no crash,
  no error, just silently-incomplete coverage.
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [meta]
repos: [unified-trading-library, deployment-service, market-tick-data-service]
scope: [engineer]
tags: [manifest-consolidator, stale-fallback, data-completeness, silent-failure, false-completion, per-vm-shards]
related:
  [
    /plans/active/issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md,
    /plans/archive/2026_08/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
  ]
created: "2026-08-07"
author: unknown
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
source: >-
  Interactive session 2026-08-07, discovered while shipping and using a new --allow-stale-fallback launcher flag to work
  around the DeFi manifest consolidator being paused for another session's long-running migration.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh,
    /plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md,
  ]
---

# `MANIFEST_ALLOW_STALE_FALLBACK` incomplete-for-long-pause gap (2026-08-07)

## What happened

1. The DeFi manifest consolidator cron (`uts-prod-manifest-consolidator-market-data-defi-cron`) had been `PAUSED` for
   ~16 hours by another session's active `canonical-migration-defi-rebuild-20260806-223130` VM (a legitimate,
   in-progress operation — correctly not interfered with, see the gas_fees issue doc's own precedent for why the cron
   pause itself was respected rather than resumed).
2. My own `dex_swaps` legacy-fold script (`fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py`) needs to read the
   manifest via `read_availability_index(..., filters=[(capture_status, ==, captured), (data_type, ==, dex_swaps)])`.
   With the consolidator this stale, every attempt raised `ManifestConsolidatorStaleError`.
3. I shipped a new `--allow-stale-fallback` flag on the launcher
   (`deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh`) that sets
   `MANIFEST_ALLOW_STALE_FALLBACK=true` for the VM's task process, reasoning (CORRECTLY, on memory-safety alone, but
   INCOMPLETELY) that since this script's read always passes `filters=`, the recovery merge would be row-group-pushdown
   bounded — i.e. safe from the OOM class of risk the guard defaults to blocking for unfiltered callers.
4. Ran it. The script completed cleanly:
   `done (apply=True). totals={'written': 22359, 'skipped_existing': 16706, 'missing_source': 26, 'manifest_registered': 22359, 'shards_ok': 260}`
   — zero errors, looks like a real completion.
5. **The `shards_ok: 260` was the tell** — the real dex_swaps worklist (measured earlier this exact session, when the
   consolidator was fresh) is ~27,549 shards / 3,459,888 captured rows across 22 venues. A direct fresh re-read using
   the SAME `MANIFEST_ALLOW_STALE_FALLBACK=true` mechanism confirmed: only **46,263 captured rows across 4 venues**
   (UNISWAP_V3, BALANCER, SUSHISWAP_V3, CURVE) were visible — under 1.4% of the real population. The script had silently
   processed a tiny fraction of the real work while reporting full, clean success.

## Root cause

`_read_slow_path`'s fallback (`unified_trading_library/manifest_writer/_read_index.py`) calls
`_read_and_merge_per_vm_shards`, which lists + merges every blob under `_index/per_vm/` — it has NO fallback to also
read the (stale, but still structurally intact) consolidated `availability_index.parquet` blob's own content. This is
correct-by-design for the mechanism's INTENDED use case (a brief, transient staleness window — e.g. a merge cycle
mid-flight — during which per-VM shards genuinely represent "everything not yet consolidated" reasonably completely). It
becomes silently wrong for a LONG staleness window, because `manifest_consolidator.py` PRUNES a per-VM shard once its
rows are confirmed merged into the consolidated index ("after a successful canonical write we prune shards whose rows
are DEFINITELY already in [it]") — so by the time a consolidator has been paused long enough for the
LAST-successful-merge's own prune to have already cleaned out everything that existed before the pause, the per-VM shard
directory only contains whatever's been written by CURRENTLY-ACTIVE writers since the pause began. Historical data isn't
lost (it's still safely in the stale consolidated blob) — it's just invisible to this specific read path.

The guard's own error message text is accurate about the memory risk ("can OOM on large buckets") but says nothing about
this completeness risk, and neither did my own launcher-flag comment when I first shipped it (already corrected in the
same commit as this doc, see Progress Log).

## Impact / who else is exposed

Any caller anywhere in the workspace that sets `MANIFEST_ALLOW_STALE_FALLBACK=true` (or `--allow-stale-fallback` on this
specific launcher) while a bucket's consolidator has been down/paused for longer than roughly one full
consolidation-and-prune cycle is at risk of the exact same false-completion signature: clean logs, zero errors, a
plausible-looking totals summary, and silently-incomplete real coverage. This is a genuinely dangerous shape of bug
because nothing about the caller's OWN output looks wrong — the only tell is comparing the processed count against an
independently-known expected population size, which most callers won't have handy.

## Recommended fix

Two independently-shippable angles:

1. **Immediate (done, same commit as this doc)**: correct the launcher flag's own comment to explicitly document this
   limitation and when it is/isn't safe to use — done in
   `deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh`.
2. **Root-cause fix (library-level, broader scope, not done)**: `_read_slow_path`'s fallback should be able to detect
   (or at minimum warn loudly on) the "consolidator has been down long enough that per-VM shards likely don't cover
   historical data" case — e.g. compare the consolidated blob's staleness age against a configured
   "prune-cycle-equivalent" threshold and refuse the fallback (or emit a CRITICAL-level warning distinct from the
   current best-effort logging) past that point, rather than silently returning a plausible-looking-but-incomplete
   DataFrame. Needs design input on the right threshold/signal (possibly: read the LAST consolidation's row count from
   the stale blob and compare against the recovered per-VM-shard row count, flagging a large mismatch).

## Todos

- [x] ✅ [INFRA] P1. Fix the launcher flag's misleading comment — done same session/commit as this doc,
      `deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh`.
- [ ] [DESIGN] P2. Decide the right detection/warning mechanism for `_read_slow_path`'s stale-fallback path to avoid
      this false-completion signature for other callers workspace-wide (not just this one launcher) — see "Recommended
      fix" angle 2 above. Needs a design call on the threshold/signal, not a bounded mechanical fix.
- [ ] [DATA] P1. **PARTIAL progress via `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`
      (2026-08-15) — precondition verified (consolidator caught up), relaunch attempted twice, both blocked by VM infra
      failures (zombie-reaped attempt, then OOM under an oversubscribed `--workers 24` — root-caused + fixed,
      `deployment-service@7480588f57`). Still open — a genuinely completed relaunch has not landed.** Follow-up (now
      unblocked by the worker-count fix):
      `plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`. The dex_swaps fold run
      that used this flag (`backfill-defi-legacy-datatype-fold-20260807-121120`, 260/27549 shards, 22,359/~3.46M rows)
      is genuinely incomplete — NOT a valid completion. Do not count it as done. Relaunch WITHOUT
      `--allow-stale-fallback` once the DeFi consolidator has genuinely caught up (wait for the
      `canonical-migration-defi-rebuild` VM's own operation to finish/resume the cron, or otherwise confirm freshness) —
      see `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 4 for the parent tracking
      context. The 260-shard partial run is harmless (additive/idempotent copy-forward, `blob_exists`-gated, no data
      corruption) — a full re-run will simply skip what's already correctly copied and cover the rest.

## Progress Log

- **interactive session 2026-08-07**: found while trying to unblock the dex_swaps legacy-fold migration against a
  long-paused DeFi manifest consolidator. Shipped the flag first with an INCOMPLETE understanding (memory-safe ≠
  data-complete — conflated the two), used it, and the `shards_ok: 260` anomaly in the otherwise-clean completion log
  was the tell that led to this root-cause. Corrected the launcher's own comment in the same session; filing this doc
  for the deeper library-level design question and to make sure the dex_swaps run isn't mistakenly counted as done.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — first verdict for this same-day doc. Read
  end-to-end; `grep -cE '^- \[ \]'` = 2, matching. Todo 1 ([DESIGN] P2, the stale-fallback detection/warning mechanism)
  needs a design call on threshold/signal per its own text; todo 2 ([DATA] P1, relaunch the dex_swaps fold) is
  dependency-blocked on the DeFi consolidator genuinely catching up (the concurrent `canonical-migration-defi-rebuild`
  VM finishing or the cron resuming) — neither is worker-determinable today.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-09 (operator ruling)**: RULED — retag `asset_group` from `[infrastructure]` to `[defi, infrastructure]` (per
  the low-confidence flag carried since 2026-08-08 in `ag_closeout_audit_infra_parked_2026_08_08.md` finding 22 /
  `ag_closeout_audit_infra_parked_2026_08_09.md` finding 6 — recommendation B taken). Frontmatter updated; content
  unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:49f9e413a4f2ed6d]: KEEP-NA, valid — todo 1
  ([DESIGN] P2) genuinely needs a design call on threshold/signal, stays NA. Todo 2 (relaunch dex_swaps fold) is
  confirmed the SAME underlying action as `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`'s
  own relaunch todo (this doc's own text already forward-points there) — that doc is in turn now tracked via
  `defi_satellite_ao_dispatch_batch14_2026_08_16.md` (see this run's marker on that doc). Not independently
  extracted — would duplicate an already-dispatched claim.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)
