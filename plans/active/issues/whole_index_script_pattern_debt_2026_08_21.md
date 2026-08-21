---
doc_type: issue
title: Whole-index manifest-script pattern debt — the AAVEV3 purge failure class is a template, not a one-off
summary: >-
  Census (2026-08-21, prompted by the AAVEV3 purge root-cause): 464 scripts across
  instruments-service/MTDS/MDPS/deployment-service/features-service read `_index/availability_index.parquet`;
  332 do a whole-frame pd.read_parquet of the downloaded bytes, only 41 stream, only 82 use any CAS, and 147
  combine whole-frame read + writes with neither CAS nor streaming. The defi index measured 7.5GB compressed /
  161.8M rows on 2026-08-21 (3.0GB on 2026-08-09 — it doubled in 12 days), and a whole-frame decode of it was
  measured at 54.5GB RSS — the exact mechanism that starved every in-VM GCS writer and got 11 AAVEV3 purge VMs
  reaped by the zombie watchdog. The pattern's SOURCE is deployment-service's migration TEMPLATES
  (template_purge/canonicalize/audit/reconcile.py, all Lifecycle permanent), so every future stamped script
  inherits it; several permanent daily tools (measure_honest_coverage.py foremost) carry it too. Fix the
  templates + shared helper + the handful of permanent tools, not the ~140 dead one-offs.
status: open
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [deployment-service, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, availability-index, memory, oom, cas, streaming, templates, zombie-watchdog]
related:
  [
    /plans/active/issues/defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-21"
author: interactive session (slot-2)
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md 2026-08-21 Progress Log (measured 54.5GB RSS whole-frame decode; zombie-watchdog reap chain), fleet grep census same session",
  ]
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/migrations/lib/templates/,
    instruments-service/scripts/measure_honest_coverage.py,
    unified-trading-library/unified_trading_library/cloud_interface/abstractions.py,
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
  ]
---

## Finding

The AAVEV3 purge failure (11 reaped VMs) was not one bad script — it is the DEFAULT pattern this fleet
stamps into every manifest script. Census 2026-08-21 (grep over `*/scripts/*.py` touching
`availability_index`; counts are pattern-presence, an upper bound, not per-line proof):

- 464 scripts touch the consolidated index; **332 whole-frame** (`pd.read_parquet` of full downloaded
  bytes), **41 streaming**, **82 any-CAS**; **147 whole-frame + writes with no CAS and no streaming**
  (87 instruments-service, 45 MTDS, 11 deployment-service, 4 features-service).
- Index growth makes the pattern newly lethal: defi `_index/availability_index.parquet` = 3.0GB
  (2026-08-09) → **7.5GB / 161.8M rows (2026-08-21)**; whole-frame decode measured **54.5GB RSS at
  T+60s** (e2-highmem-8, supervised run) — memory-livelocks 32GB hosts outright, starves every in-VM
  GCS writer (heartbeat sidecar included), and the zombie watchdog then reaps the "dark" VM at the
  15-min default window.
- **Root of the spread: the migration templates are the pattern's SSOT.**
  `deployment-service/scripts/migrations/lib/templates/{template_purge,template_canonicalize,
  template_audit,template_reconcile}.py` — all `Lifecycle: permanent` — carry whole-frame + no-CAS, so
  every future stamped one-off inherits the defect. Most of the 147 risky scripts are dated executed
  one-offs (dead weight pending deletion), so fixing THEM is low-value; fixing the templates fixes the
  future.
- **Permanent/recurring tools carrying the risky pattern** (these DO run again, against ever-bigger
  indexes): `instruments-service/scripts/measure_honest_coverage.py` (DAILY — produces coverage.json),
  `build_instrument_catalogue.py`, `reconcile_phantom_manifest_rows_all.py`, `rescan_sports_manifest.py`,
  `split_prediction_by_market.py`, `market-tick-data-service/scripts/sweep_phantom_manifest_rows.py`,
  `deployment-service/scripts/wave_launcher.py`,
  `deployment-service/scripts/migrations/market-tick-data-service/reconcile_market_tick_manifest.py`.
- Adjacent infra gaps (same incident class): `launch-canonical-migration-vm.sh` default
  `e2-standard-8` (32GB) for whole-index CAS rewrites sized for the 2.41GiB-era index; whole-index
  `bucket=None` VM prefixes with NO `PREFIX_IDLE_THRESHOLDS` entry (`defi-manifest-force-consolidate-`
  — registry notes OOM history, `defi-manifest-projection-`, `mdps-cefi-manifest-merge-`,
  `backfill-candle-manifest-{cefi,defi,prediction,tradfi}-`, `cefi-itype-casing-apply-rw-`); `KEEP_VM`
  supervised-diagnostic mode exists only in the AAVEV3 launcher, not `launcher_common.sh`.
- NOT at risk by this mechanism: UTL `manifest_consolidator.py` (DuckDB streaming reads +
  `if_generation_match` lock already), though its `_LEGACY_SEED_PATH` branch still whole-downloads
  index bytes.

The proven replacement pattern (shipped + verified in
`instruments-service/scripts/purge_defi_aavev3_bare_alias_manifest_rows_2026_08_20.py`, 2026-08-21):
`download_bytes_with_generation` → temp file → `pq.ParquetFile.iter_batches` (~2GB peak measured on the
161.8M-row index) → pandas mask on a few-column view only → Arrow-layer filter →
`conditional_upload_bytes(if_generation_match=<scan generation>)`, plus a server-side exact-bytes
`gcs_copy_object` snapshot.

## Todos

- [ ] [CODE] P1. Port the streaming + CAS pattern into the four migration templates
      (`deployment-service/scripts/migrations/lib/templates/template_{purge,canonicalize,audit,
      reconcile}.py`) so every future stamped script inherits it — mirror the proven AAVEV3 purge
      script structure (generation-pinned read, iter_batches scan, few-column mask view, Arrow filter,
      CAS write, server-side snapshot).
- [ ] [CODE] P2. `measure_honest_coverage.py` (daily, permanent): RE-SCOPED 2026-08-21 after a deeper
      read — the census's coarse regex overcounted its risk: it ALREADY column-projects
      (`_read_parquet_safe`, 5-6 columns) and preserves dictionary encoding, and its dedicated VM was
      already OOM-bumped to e2-highmem-8/64GB on 2026-08-15 after a measured 31.68GB anon-rss peak on
      32GB. Remaining work is headroom VERIFICATION under index growth (defi doubled to 7.5GB in 12
      days — re-measure peak RSS on the next scheduled run vs the 64GB ceiling), not an urgent rewrite.
- [ ] [CODE] P2. Same conversion for the remaining permanent-lifecycle whole-frame tools listed in the
      Finding (catalogue builder, phantom reconcilers/sweepers, sports rescan, prediction split,
      wave_launcher, MTDS manifest reconcile) — one PR per repo, shared helper preferred.
- [ ] [DESIGN] P2. Decide the shared-helper home (UTL `manifest_index_io`-style:
      `stream_availability_index(bucket, columns, batch_size)` + `rewrite_availability_index_cas(...)`)
      and whether a QG ratchet should ban NEW whole-frame index reads in `scripts/` (baseline-only-down,
      matching existing ratchet conventions).
- [ ] [INFRA] P3. `launch-canonical-migration-vm.sh`: REFINED 2026-08-21 — a blanket default bump off
      `e2-standard-8` (32GB) was deliberately NOT shipped: the launcher also runs per-shard STREAMING
      content passes for which 32GB is right-sized, and a blanket bump would oversize the common case.
      The correct change is category-scoped: size only the whole-index categories (index
      download+filter+rewrite CAS ops) to 64GB, keyed on the category/task flag at launch — make that
      call when next actually running one against today's 7.5GB+ indexes.
- [ ] [INFRA] P2. Add `PREFIX_IDLE_THRESHOLDS` entries for the whole-index `bucket=None` prefixes named
      in the Finding (same `(90, 360)` shape as `canonical-migration-` / `defi-aavev3-bare-alias-purge-`),
      then relaunch the zombie-watchdog VM once (its running copy never re-fetches).
- [ ] [INFRA] P3. Generalize `KEEP_VM=true` (shutdown=false + `keep=true` label) from
      `launch-defi-aavev3-bare-alias-purge-vm.sh` into `lib/launcher_common.sh` so any launcher gets a
      supervised-diagnostic mode without a per-copy edit.

## Progress Log

- **2026-08-21 (interactive session, slot-2)**: census run + doc created directly off the AAVEV3
  root-cause session (see related issue's 2026-08-21 Progress Log for the measured mechanism). No code
  changed under this issue yet; the AAVEV3 purge script itself is the reference implementation.
- **2026-08-21 (same session, later — templates + infra AUTHORED, ship pending)**: implemented in the
  slot-2 deployment-service tree (all `py_compile`/`bash -n` clean; full QG in flight; COMMIT BLOCKED
  behind the same peer UAC migration as the AAVEV3 [SHIP] P1 todo — these files ride that ship):
  - `migration_common.py`: new whole-index safety helpers — `download_index_with_generation` /
    `download_bytes_with_generation` (one consistent GET: content + CAS pin),
    `stream_filter_parquet` (record-batch streaming scan/filter, bounded ~1M-row peak, Arrow-layer
    kept-row writes, per-batch `on_batch` stats hook), `cas_upload_bytes` (raises
    `ManifestCasConflictError` on a lost generation race), `snapshot_object_serverside` (exact-bytes
    server-side snapshot).
  - `template_purge.py`: REQUIRED `PurgeConfig.predicate_scope` (`"row_local"` streams via the new
    helpers; `"whole_frame"` keeps legacy semantics for cross-row predicates, now with a stated
    memory budget); BOTH scopes CAS-write pinned to the read generation; snapshots are server-side
    copies; `manifest_index_updater` overrides are whole_frame-only (loud ValueError otherwise).
    `tests/unit/test_template_purge.py` rewritten: both scopes parameterized, real pyarrow streaming
    exercised (not mocked), CAS-pin/conflict/ordering/required-scope coverage added.
  - `template_canonicalize.py` / `template_reconcile.py` / `template_backfill.py`: generation-pinned
    reads + CAS write-backs (canonicalize CAS-pins only the in-place case; a different output path
    stays a plain fresh-object write), backfill's snapshot switched to the server-side copy; explicit
    whole-frame memory notes. Streaming for these three remains open ([DESIGN] P2's shared-helper
    adoption) — their transform/comparator hooks take whole frames by contract.
  - Consumers updated in-change: `purge_bad_prediction_manifest_rows.py` + the purge worked example
    pin `predicate_scope="whole_frame"` (bit-identical legacy behavior; the example's "superseded"
    predicate is genuinely cross-row).
  - `vm_zombie_watchdog.py`: idle-threshold entries added for the remaining whole-index bucket=None
    prefixes (`defi-manifest-force-consolidate-`, `defi-manifest-projection-`,
    `mdps-cefi-manifest-merge-`, `backfill-candle-manifest-`, `cefi-itype-casing-apply-rw-`), same
    (90, 360) shape as `canonical-migration-`; requires the one-time watchdog VM relaunch already
    tracked in the AAVEV3 [SHIP] P1 todo.
  - `lib/launcher_common.sh`: `KEEP_VM=true` supervised-diagnostic mode generalized into
    `lc_gcloud_create` (metadata flip + `keep=true` label) — every launcher inherits it.
  - Census corrections applied above per measurement-claims discipline: `measure_honest_coverage.py`
    re-scoped to P2 headroom-verification (already column-projected + on a 64GB VM since 08-15);
    canonical-migration sizing refined to category-scoped (blanket bump rejected as oversizing its
    streaming content passes).
