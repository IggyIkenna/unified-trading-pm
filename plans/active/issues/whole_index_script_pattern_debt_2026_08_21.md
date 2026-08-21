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

- [x] [CODE] P1. ✅ DONE 2026-08-21 — LANDED as `deployment-service@3000d17ccc` (full isolated re-gate
      green: templates purge/canonicalize/reconcile/backfill + `migration_common` streaming/CAS seams +
      5 template test files + 2 consumers declaring `predicate_scope`). Port the streaming + CAS pattern into the four migration templates
      (`deployment-service/scripts/migrations/lib/templates/template_{purge,canonicalize,audit,
      reconcile}.py`) so every future stamped script inherits it — mirror the proven AAVEV3 purge
      script structure (generation-pinned read, iter_batches scan, few-column mask view, Arrow filter,
      CAS write, server-side snapshot).
- [x] [CODE] P1. ✅ INTERIM RESOLVED 2026-08-21 — launcher default raised e2-highmem-8 -> e2-highmem-16
      (128GB, the size that succeeded same-day while 64GB OOM'd) in `deployment-service@6ef5ba27c2`;
      GCS launcher copy republished same hour so the 00:30 UTC nightly picks it up. Residuals: the
      usage-comment at the launcher's line ~31 still says highmem-8 (fix with the next DS touch), and
      the durable streaming conversion moved into the [CODE] P2 conversion todo below. Original:
      `measure_honest_coverage.py` (daily, permanent): headroom question ANSWERED THE HARD
      WAY same day — an `--asset-group all` run on the standard e2-highmem-8/64GB VM was OOM-KILLED
      (rc=137, `measure-honest-coverage-20260821-091926`, kernel `Killed`) right at the defi index
      load (161,763,519 rows), despite the script's existing column-projection + dictionary
      preservation. **The scheduled nightly is therefore BROKEN at today's index size** until either
      (a) the launcher default machine (and whatever the scheduler passes) is raised — a one-line
      deployment-service change (the AAVEV3 [SHIP] batch has LANDED at `3000d17ccc`; ship the bump
      standalone) — or (b) the read path is converted to
      streaming (`migration_common.stream_filter_parquet`-style per-batch aggregation), the durable
      fix. A 128GB (`--machine-type e2-highmem-16 --oom-monitor`) run was used same-day to produce
      2026-08-21's coverage.json and to capture the real peak for sizing; check its oom-monitor trail
      before choosing the interim machine default. (Historical note kept for context: 32GB peaked at
      31.68GB anon-rss on 2026-08-08's index; the 08-15 bump to 64GB has now been outgrown too.)
- [ ] [CODE] P2. Same conversion for the remaining permanent-lifecycle whole-frame tools listed in the
      Finding (catalogue builder, phantom reconcilers/sweepers, sports rescan, prediction split,
      wave_launcher, MTDS manifest reconcile) PLUS `measure_honest_coverage.py` (its 2026-08-21
      interim was a machine bump to 128GB; at the index's measured doubling rate that buys months,
      not years) — one PR per repo, shared helper preferred.
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
- [x] [INFRA] P2. ✅ DONE 2026-08-21 — six prefix entries LANDED in `deployment-service@3000d17ccc`;
      zombie-watchdog VM relaunched (old `…20260815-191525` deleted → after two daemon-less boots
      from the tarball boot-breaker below, `vm-zombie-watchdog-20260821-164521` RUNNING, daemon
      VERIFIED sweeping 16:03Z; the launcher re-uploads the `.py` SSOT on every launch). Add
      `PREFIX_IDLE_THRESHOLDS` entries for the whole-index `bucket=None` prefixes named in the Finding
      (same `(90, 360)` shape), then relaunch the zombie-watchdog VM once.
- [x] [INFRA] P3. ✅ DONE 2026-08-21 — LANDED in `deployment-service@3000d17ccc` (`lc_gcloud_create`:
      `KEEP_VM=true` → `VM_SHUTDOWN_ON_COMPLETION=false` + `keep=true` label). Generalize `KEEP_VM=true` (shutdown=false + `keep=true` label) from
      `launch-defi-aavev3-bare-alias-purge-vm.sh` into `lib/launcher_common.sh` so any launcher gets a
      supervised-diagnostic mode without a per-copy edit.

- [ ] [INFRA] P1. Code-tarball publish pipeline hardening (2026-08-21 incident — fleet-wide VM-boot
      breaker, root-caused by measurement): the 14:08Z republish wave shipped `deployment-service` /
      `unified-api-contracts` tarballs built on a Mac WITHOUT `COPYFILE_DISABLE` and WITHOUT excluding
      `.claude/` — thousands of AppleDouble `._*` members (+ a swept-in `.claude/worktrees/<agent>/`
      tree) made GNU tar on the VM emit enough warnings that the bootstrap's
      `tar xf ... 2>&1 | head -5 || true` SIGPIPE'd tar mid-extraction -> truncated tree without
      `pyproject.toml` -> `pip_install_or_fail` FATAL -> the zombie-watchdog VM booted daemon-less
      TWICE (13:5x boot: DS tarball; 14:13 reset boot: UAC tarball; a clean-tree republish restored
      coverage the same hour — the fleet had NO zombie watchdog for ~30 min). Fixes: (a)
      `create-code-tarballs.sh` must set `COPYFILE_DISABLE=1` + exclude `.claude/`, and REFUSE to
      publish a tarball containing `._*` members (a post-build scratch-venv install self-check would
      have caught every variant); (b) same script crashed on unset `GCP_PROJECT_ID` mid-run yet still
      exited 0 — make it fail loudly; (c) the VM bootstraps' `tar xf ... 2>&1 | head -5` pattern must
      not let head's SIGPIPE truncate extraction (log to file, tail the file — same class as the
      2026-08-16 `pip_install_or_fail` fix, one seam earlier: launch-vm-zombie-watchdog.sh's heredoc +
      grep the sibling setup-*.sh bootstraps for the same pattern). PARTIAL SHIP 2026-08-21: (a)+(c)
      LANDED as `deployment-service@e0c38258` — builder gained `COPYFILE_DISABLE=1` + `--no-xattrs` +
      a `.claude` exclude; the launcher's 3 extraction sites now log to file with
      `--warning=no-unknown-keyword` (setup-data-pipeline-vm.sh grep'd clean — no tar-pipe-head there).
      Clean tarballs republished 15:45Z (verified: 0 PAX xattr headers, pyproject at depth); the
      watchdog boot on the fixed pair went straight through to a live sweeping daemon (16:03Z).
      REMAINING in this todo: (b) fail-loud on unset `GCP_PROJECT_ID` (measured: it crashed mid-run
      yet exited 0), the publish-time self-check (refuse `._*`/xattr'd members, scratch-venv install
      smoke), and IDENTIFY the recurring wrong-cwd Mac republisher (waves at 13:15Z / 14:08Z / ~15:2xZ
      kept clobbering clean generations — until it pulls `e0c38258` its output stays poisonous).

## Progress Log

- **2026-08-21 (interactive session, slot-2)**: census run + doc created directly off the AAVEV3
  root-cause session (see related issue's 2026-08-21 Progress Log for the measured mechanism). No code
  changed under this issue yet; the AAVEV3 purge script itself is the reference implementation.
- **2026-08-21 (same session, later — templates + infra AUTHORED, ship pending)**: implemented in the
  slot-2 deployment-service tree (all `py_compile`/`bash -n` clean; QG verdict: the batch itself is
  GREEN — all 5 template test files pass, 0 template/migration failures; the tree's remaining 41
  pytest failures are the same upstream dep-drift baseline the peer's in-flight UAC migration causes
  fleet-wide, unchanged by this batch; COMMIT BLOCKED behind that migration, same as the AAVEV3
  [SHIP] P1 todo — these files ride that ship):
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
- **2026-08-21 (same session, final — honest-coverage rollup REFRESHED post-purge)**: today's
  `gs://central-element-323112-honest-coverage/2026-08-21/coverage.json` VERIFIED at updated
  09:18:34Z (after the 06:38Z AAVEV3 purge): all 5 asset_groups measured, 0 failed, **0 `AAVEV3`
  occurrences** (canonical `AAVE_V3` present) — deployment-api's honest-coverage surface now serves
  post-purge numbers; the `/api/data-status/manifest` rollup was separately verified to never have
  carried the phantom (registry-driven venue universe). Getting there took 6 launch attempts whose
  real blocker was TARBALL-SET CONSISTENCY: floating tarballs had drifted to mixed vintages (a
  fresh-UTL/stale-UAC skew import-crashed one run on `MarginModel.DERIBIT`), and per-repo
  auto-republish can't fix it while trees are dirty (peer UAC WIP + this session's own in-flight
  work) — solved by building the whole set from clean DETACHED WORKTREES at landed HEADs
  (`git worktree add --detach` + `WORKSPACE_ROOT=<clean-ws> create-code-tarballs.sh --include
  instruments-service`), a reusable recipe when shared trees are dirty. ATTRIBUTION CAVEAT kept
  honest: one 64GB all-AG run today was OOM-killed (rc=137) at the defi-index load, and the
  successful 09:18Z write came from a SUBSEQUENT run launched with the consistent tarballs (most
  plausibly the ~09:10 nightly) — before trusting the nightly as healed, the [CODE] P1 todo above
  must confirm which machine size wrote 09:18Z and whether the launcher/scheduler default still
  needs the bump.
