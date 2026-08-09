---
doc_type: audit-instruction
title: data_pipeline_e2e_check_audit_instructions
summary:
  Operator-triggered real-infra smoke check verifying instruments-service + MTDS backfill force-refetch and
  skip-if-fresh actually work (never just against `-test-` buckets in isolation), for both batch and live modes, across
  every MVP (asset_group, venue[, data_type]) shard — run via the `/data-pipeline-check-is` +
  `/data-pipeline-check-mtds` skills, never wired into `quality-gates.sh`.
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [audit, data-pipeline, smoke-test, e2e, instruments-service, mtds, backfill, force-skip, live-mode, vm-launcher]
related:
  [
    ../../active/data_pipeline_e2e_check_2026_07_10.md,
    ../../epics/infrastructure_master.md,
    ../../../cursor-configs/skills/data-pipeline-check-is/SKILL.md,
    ../../../cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
  ]
created: 2026-07-10
tier: L3
parent_epic: infrastructure_master
cadence: occasionally-scheduled (operator-triggered), not fixed
verifier:
lifespan:
type: audit-instructions
epic: infrastructure_master
assigned_vm: NA
last_updated: 2026-07-10
---

# Data-pipeline e2e check — audit instructions

## Epic Scope

Real-infra proof (not a `-test-`-bucket-only dev smoke test) that instruments-service's and MTDS's backfill CLI paths
genuinely (a) refetch a genuinely-missing shard when `--force`d, (b) skip an already-captured shard via skip-if-fresh
logic without a wasted re-download, and (c) hold under `--mode live`. Writes are always `-test-`-bucket-scoped
(`IS_TEST_RUN=true` via `get_write_bucket_name()`); a pre-check step may read PROD to decide what's genuinely
missing/captured, but never mutates PROD. Shard granularity matches each service's real partition atom: IS =
`(asset_group, venue, day)` (SPORTS: `(sports_provider, day)`), no instrument-level split; MTDS = the real 6-tuple
`(asset_group, venue, data_type, day)` + one sampled `instrument_id`/underlying-root, with a genuine Sports `league_id`
axis. Owned by `infrastructure_master` because the shared engine (`unified_trading_library.pipeline_e2e_check`) is
cross-service infra, and the VM launchers it drives (`launch-instruments-backfill-vm.sh`, `launch-mtds-backfill-vm.sh`)
are already-registered `VM_PREFIX_TO_BUCKET` entries this epic owns.

Codex SSOTs: `/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/05-infrastructure/spot-vms-for-backfill.md`,
`/codex/05-infrastructure/gcs-object-operations.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/04-architecture/tier-and-import-architecture.md`.

## Triggers

- Occasionally-scheduled (operator-triggered) — not a fixed cadence today. Future: cron-schedulable via the `schedule`
  skill once the engine has proven stable across a few manual runs.
- After any change to `unified_trading_library/pipeline_e2e_check/` (the shared engine).
- After any change to `launch-instruments-backfill-vm.sh` / `launch-mtds-backfill-vm.sh` (the launcher diffs this check
  depends on: `--venues`/`--vm-name`/`--test-run`/`--instrument-ids`).
- After any change to `get_write_bucket_name()` / `_resolve_freshness_bucket()` / `get_tick_data_bucket()` (the IS/MTDS
  read-bucket asymmetry this check's skip-leg semantics depend on).
- After a new asset_group's `-test-` buckets are first provisioned (Phase 0 gate) — re-run to confirm the new
  asset_group's full matrix, not just the provisioning step.
- Before onboarding a 3rd service (e.g. features-service) onto the shared engine — run IS + MTDS once more to confirm no
  regression before extending the pattern.

## Checklist

- [ ] (a) **Phase-0 provisioning gate is genuinely enforced, not assumed.** For all 5 asset_groups × 2 services,
      `gs://instruments-store-{ag}-test-{pid}` and `gs://market-data-tick-{ag}-test-{pid}`
      (`market-data-tick-pred-test-{pid}` for prediction) exist. Run:
      `gcloud storage buckets describe gs://instruments-store-{ag}-test-central-element-323112` for each `ag` — a
      missing bucket is a real finding (must be provisioned before Phase 1), never a silent skip.

- [ ] (b) **Force-leg proved real refetch for every MVP shard (IS).** For every MVP `(asset_group, venue)` cell: the
      force-leg VM reached `EXIT_STATUS=SUCCESS`, the `-test-` bucket parquet was (re)written, and the manifest row
      shows `captured`. Evidence: the shard's row in `plans/audit/results/data_pipeline_e2e_check_is_<date>.md` shows
      `force: PASS` with a fingerprint/timestamp that changed vs. the shard's pre-force state.

- [ ] (c) **Skip-leg proved real skip-if-fresh for every MVP shard (IS) — self-contained proof.** Immediately following
      (b) on the SAME shard with no `--force`: the skip-leg VM logs the IS freshness-preflight skip signal, and the
      `-test-` bucket object's fingerprint (generation + `updated`) is **unchanged** from the force-leg. Because
      `IS_TEST_RUN=true` routes both the freshness read and the write to the same `-test-` bucket, this is a complete,
      self-contained proof — no PROD pre-check required for IS.

- [ ] (d) **Force-leg proved real refetch for every MVP shard (MTDS).** For every MVP
      `(asset_group, venue, data_type)` cell (Sports enumerated per `league_id`, never collapsed): the force-leg VM
      reached `EXIT_STATUS=SUCCESS` with a real sampled `instrument_id` (never hardcoded), the `-test-` bucket parquet
      was (re)written, and the manifest row shows `captured`.

- [ ] (e) **Skip-leg proved genuine (prod-captured) for every MVP shard (MTDS) — labeled, not assumed.** MTDS's
      freshness read is PROD-driven (`_resolve_freshness_bucket()` ignores `IS_TEST_RUN`), so a skip-leg only proves
      something real when its target shard/day was already verified captured in PROD via
      `prod_precheck.read_prod_capture_status()`. Every skip-leg row in the report MUST carry
      `skip_proof: genuine (prod-captured)` when the pre-check found a PROD-captured shard/day, or
      `skip_proof: ambiguous` otherwise. **RED if any skip-leg row is missing this label, or claims `genuine` without a
      PROD-precheck citation.** Deliberately re-run against one known PROD-uncaptured shard/day and confirm it is
      labeled `ambiguous`, not `genuine`.

- [ ] (f) **Live-leg proved for every MVP venue (both services).** `--legs live --mvp-only` ran for every MVP venue in
      `unified_api_contracts.canonical.crosscutting.mvp_scope.is_mvp()` scope, on both IS and MTDS, writing only to the
      `-test-` bucket sibling, with a `live: PASS` verdict recorded per venue.

- [ ] (g) **No PROD mutation anywhere in the run.** Grep the run's launcher invocations for `--test-run` on every leg
      (force/skip/live) of every shard in the report; confirm no launcher call omitted it.

- [ ] (h) **Neither script is wired into its service's `quality-gates.sh`.** Grep:
      `rg "pipeline_e2e_check" instruments-service/scripts/quality-gates.sh market-tick-data-service/scripts/quality-gates.sh`
      — 0 hits in both. This check does real I/O + real VM spend + multi-minute-plus runtime by design; it stays a
      standalone, on-demand skill.

- [ ] (i) **VM registry hygiene.** The `-pipelinecheck-<run_ts>`-suffixed VM names still match the registered
      `instr-backfill-{ag}-` / `mtds-backfill-{ag}-` prefixes in `VM_PREFIX_TO_BUCKET`
      (`deployment-service/scripts/vm/vm_zombie_watchdog.py`) — confirm a dry-run of the zombie watchdog raises no
      "unregistered VM" warning for any check-run VM name, and that every launched VM actually stopped
      (`VM_SHUTDOWN_ON_COMPLETION=true`).

## Success Criteria

- Checklist items (a)–(i) all GREEN for the audited day.
- Every MVP `(asset_group, venue)` cell (IS) and `(asset_group, venue, data_type[, league_id])` cell (MTDS) in the
  matrix for the audited day carries a force verdict, a (labeled, for MTDS) skip verdict, and a live verdict — no cell
  silently absent from the report.
- Zero PROD writes across the entire run (test-bucket-only, per (g)).
- Zero zombie/unregistered VMs left behind (per (i)).

## Output Format

The audit result file must contain:

- Checklist results (a)–(i), each GREEN / AMBER / RED + evidence (grep output, report-file excerpt, `gcloud` command
  output).
- A cited pointer to the two run reports produced by the skills:
  `plans/audit/results/data_pipeline_e2e_check_is_<YYYY_MM_DD>.md` and
  `plans/audit/results/data_pipeline_e2e_check_mtds_<YYYY_MM_DD>.md` (the primary machine-readable evidence — this audit
  reviews them, it does not re-derive their content).
- Any new gap items, expressed as `- [ ] [TYPE] P#. ...` ready to paste into an active plan, with
  `parent_epic: infrastructure_master` (or the relevant asset_group epic if the gap is shard-specific to one
  asset_group).
- Recommended active plan title for each gap.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
