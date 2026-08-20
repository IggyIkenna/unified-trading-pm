---
doc_type: plan
title: Infra satellite — lc_gcloud_create migration for the remaining raw-create VM launchers (batch 17)
summary: >-
  Follow-up plan for `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s P3 todo ("dedicated migration plan for
  remaining ~136 raw-create launchers to `lc_gcloud_create`"). Re-measured the corpus fresh against current
  deployment-service HEAD rather than trusting the issue doc's 2026-07-31 numbers: 149 launchers (not ~136) still call
  `gcloud compute instances create` directly (10 already use `lc_gcloud_create`). Splits the corpus into a directly
  migratable tier (45 launchers, no blocking gap against the current wrapper signature — dispatched here as 3 AO todos)
  and three genuinely blocked tiers gated on operator design decisions this plan does NOT resolve unilaterally: SPOT
  provisioning (79 launchers — a bigger, previously-undocumented gap: `lc_gcloud_create` has ZERO
  `--provisioning-model`/`--instance-termination-action` support at all), `--metadata-from-file` (47 launchers, not just
  "e.g. one shutdown script" as the source issue framed it), and `--boot-disk-type` (135 launchers pass the flag, but
  nearly all of them just echo the wrapper's own would-be default). The source issue's "large-disk / `${BOOT_DISK_SIZE%GB}`
  extraction" framing was itself stale — measured 0/149 launchers use that pattern; `disk_gb` is already a plain
  positional arg on `lc_gcloud_create`, so that tier does not exist as a real blocker.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, vm-launcher, lc_gcloud_create, satellite, batch-17]
related:
  [
    /plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    /plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Follow-up todo in `vm_launcher_setup_script_freshness_gap_2026_07_31.md` ("[SCRIPT] P3. Follow-up: dedicated
  migration plan for remaining ~136 raw-create launchers to lc_gcloud_create"), authored 2026-08-16 (slot 9, infra),
  per that todo's own 2026-08-12 ao-readiness clarification: author + dispatch a fan-out plan, but do not silently
  resolve the open design forks — carry them as their own [REVIEW]/[OPERATOR] todos.
---

# Infra satellite — lc_gcloud_create migration, batch 17

## Why this plan exists

`vm_launcher_setup_script_freshness_gap_2026_07_31.md` found only 4 (now 10, after batch-1's first 3-launcher migration
plus the freshness-gap fix itself) of 143+ VM launchers call the `lc_gcloud_create` wrapper — the only path that
auto-inherits `lc_verify_setup_script_freshness`, `lc_verify_canonicalisation_gate`, and the standardized `managed-by`
label. The other raw-`gcloud compute instances create` callers get none of these guards. That issue doc's own P3 todo
asked for a dedicated migration plan rather than a 136-file sweep folded into one bounded todo; this is that plan.

**Re-measured against current HEAD** (`grep -l "gcloud compute instances create" scripts/vm/*.sh`, excluding lib/helper
files and existing `lc_gcloud_create` callers): **149 raw-create launchers remain**, not ~136 — the corpus grew between
2026-07-31 and today. Reading `lc_gcloud_create`'s actual signature (`launcher_common.sh:528-611`) against that corpus
found the blocking-gap shape is different from the source issue's framing:

| Tier                             | Count | Blocking?                                                                                     |
| --------------------------------- | ----: | ---------------------------------------------------------------------------------------------- |
| Directly migratable today         |    45 | No — current signature already covers them                                                    |
| `--provisioning-model=SPOT` users |    79 | **Yes — `lc_gcloud_create` has NO Spot support at all** (not in the source issue's 3 tiers)     |
| `--metadata-from-file` users      |    47 | Yes — wrapper only accepts inline `metadata_str`, no file-based metadata                        |
| `--boot-disk-type` passers        |   135 | Mostly not — see todo 3, nearly all just echo the GCE default                                   |
| `${BOOT_DISK_SIZE%GB}`-style users |    0 | N/A — source issue's "large disk" tier does not exist; `disk_gb` is already a plain numeric arg |

(Tiers overlap — SPOT and metadata-from-file are the two real blockers; a launcher can carry both plus a `--boot-disk-type`
line and still land in "directly migratable" once tiers 1/2 clear it does not.)

## Rules this plan follows

Same discipline as `infra_satellite_ao_dispatch_batch1_2026_07_26.md`: same-priority todos touch disjoint file sets (the
45 direct-candidates are split into 3 non-overlapping groups of 15); `sequential:` unset; the two/three genuinely open
design questions are `[OPERATOR]`/`[REVIEW]` todos, not resolved here. The SPOT-tier and metadata-from-file-tier
migrations themselves are **not** drafted as todos in this plan — they are blocked on todos 1/2 below and belong in a
follow-up batch once the operator rules (see `## Deferred`).

## Todos

- [x] ✅ [DATA] P1. **RULED 2026-08-16 (operator, na-eligibility-audit follow-up): option (a) — add optional
      `provisioning_model`/`instance_termination_action` params to `lc_gcloud_create` directly (backward compatible —
      omit both, unchanged behavior for the 10 current non-Spot callers).** Not (b) a parallel wrapper (avoids logic
      drift between two VM-launch code paths — a single source of truth is what makes the dedup/resume-from-progress
      guarantees below actually verifiable) and not (c) carving Spot launchers out permanently. Operator's standing
      policy: **SPOT everywhere by default, non-SPOT is the exception and must be tracked in the launcher registry**
      (`VM_PREFIX_TO_BUCKET` or equivalent), not left as an undocumented per-script deviation.
      **Bundled requirement (operator, same ruling) — this migration must also verify, not just implement**:
      (1) auto-relaunch after preemption resumes from measured PROGRESS, never replays `START_DATE` from scratch (per
      `/codex/05-infrastructure/spot-vms-for-backfill.md` — this is a STANDING rule, not new, but explicitly re-flagged
      here because it's exactly the class of bug a provisioning-model refactor could silently break);
      (2) the idempotent-skip-existing-without-`--force` check must be evaluated and TESTED (not just asserted) before
      any of the 79 launchers ship on the new wrapper — write a regression test proving a second launch attempt against
      an already-running/already-done shard does NOT create a duplicate VM. Both are part of the standing VM-management
      discipline `cursor-configs/CLAUDE.md` § "Launching VMs / infra" points at
      (`/codex/05-infrastructure/vm-launcher-runbook.md`) — this todo's done-when includes updating that runbook if the
      testing surfaces a gap in its documented guarantees, not just landing the provisioning-model code change.
      **Shipped**: added optional 9th/10th positional args `provisioning_model`/`instance_termination_action` to
      `lc_gcloud_create` (`launcher_common.sh`) — additive-only, both real `gcloud compute instances create`
      invocations only gain `--provisioning-model=…`/`--instance-termination-action=…` when non-empty; verified
      byte-identical dry-run + real-invocation output when omitted (`TestSpotProvisioningParams`,
      `test_backward_compatible_when_omitted` + `test_omitted_flags_never_appear_in_the_real_gcloud_invocation`).
      Bundled requirement (1) — no code change needed: `RelaunchPreemptedVm` replays captured `LAUNCH_PARAMS.json`
      independently of this wrapper, so the PROGRESS-checkpoint resume contract is unaffected by this change (verified
      by reading the resume path, not just asserted). Bundled requirement (2) — wrote
      `TestSpotIdempotentSkipExisting` (2 tests): confirms a second launch attempt against a shard whose VM is
      RUNNING is refused by `lc_singleton_check` before `lc_gcloud_create` is ever reached (no duplicate create call),
      and that a shard whose VM is no longer RUNNING is free to relaunch (duplicate *work*, not a duplicate *VM*, is
      then prevented by the backfill's own manifest presence-skip downstream — documented explicitly in the test).
      Updated `vm-launcher-runbook.md`'s Known Issues with the new params + what was verified. Full suite
      (`test_vm_launcher_scripts.py`, 246 tests) green; `quality-gates.sh` green (245s). Shipped —
      deployment-service@274233a891. Repo: deployment-service.

- [ ] [OPERATOR] P1. **Resolve the `--metadata-from-file` design fork (47 of 149 launchers — not just "e.g. one
      shutdown script" as the source issue framed it).** `lc_gcloud_create` only accepts an inline `metadata_str`
      (positional arg 6); it has no file-based-metadata path. Options:
      (a) add an optional `metadata_from_file` param (mutually exclusive with `metadata_str`, or additive per gcloud's
      own semantics — gcloud allows combining `--metadata` and `--metadata-from-file` for different keys, so check
      whether that combination is actually needed across the 47 or whether each launcher uses one exclusively);
      (b) drop file-based-metadata launchers from this migration's scope and document why (mirrors the source issue's
      original framing, just scoped to the real 47-launcher count instead of "one script").
      **Done when**: the operator states a decision (a/b), same closure mechanism as the SPOT todo above. Repo:
      unified-trading-pm (decision only). Source: `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s tier (3),
      re-measured.

- [x] ✅ [REVIEW] P2. **Resolve the `--boot-disk-type` design fork — reviewed 2026-08-16 (slot 12, review craft).**
      Ran the full corpus (140 of 149 files match `boot-disk-type`, not a 15-file sample — cheap enough to do
      exhaustively): `grep -h boot-disk-type scripts/vm/*.sh | sort | uniq -c`. Confirmed **~124 launchers** genuinely
      default via `${BOOT_DISK_TYPE:-pd-balanced}` (or the tradfi-ohlcv lib's `${TRADFI_OHLCV_BOOT_TYPE:-pd-balanced}`,
      which resolves the same way) with **zero external override** anywhere in the repo
      (`grep -rn "BOOT_DISK_TYPE=" --include='*.sh' --include='*.yml' --include='*.yaml' .` outside `scripts/vm/`, and
      no caller of `_tradfi-ohlcv-launcher-lib.sh` sets `TRADFI_OHLCV_BOOT_TYPE` — both 0 hits) — **recommendation
      "document pd-balanced default as sufficient" APPROVED for these ~124.**
      **BUT found a genuine-override tier the sample-of-2 in the original todo text missed: 15 launchers HARDCODE a
      non-default disk type** (14 × `--boot-disk-type=pd-ssd`, 1 × `--boot-disk-type=pd-standard` on
      `launch-planning-vm.sh`) — not env-defaulted, a deliberate literal choice, and `lc_gcloud_create`
      (`launcher_common.sh`) confirmed to never pass `--boot-disk-type` at all (0 grep hits), so migrating any of these
      15 through the wrapper as it stands today silently drops them to GCE's bare default (pd-balanced) — a real
      regression, not a no-op. See the new `[OPERATOR]` todo below (not resolved unilaterally, same pattern as todos
      1/2). **Live conflict found + already flagged**: one of the 15, `launch-funding-ensemble-paper-cron-vm.sh`, is
      also listed in todo "Migrate group B" below as a directly-migratable file — pinged slot 17 (owner of the Group B
      task, `infra_satellite_ao_dispatch_batch17-b8c1c8dc93f6`, dispatched at time of this review) directly via
      `/api/slots/17/message` to exclude that one file from their migration; not editing Group B's own file list here
      since it's a live dispatched task. Repo: unified-trading-pm. Source:
      `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s tier (2).

- [x] ✅ [OPERATOR] P2. **DONE 2026-08-19 (`/plan-reconcile security_and_cross_cutting_master` Phase 2 flip — the
      todo's own stated done-when, "the operator states a decision," was already satisfied by the DECIDED line below,
      just never flipped).** **Resolve the pd-ssd/pd-standard genuine-override tier (15 of 149 launchers) — found during the
      `--boot-disk-type` review 2026-08-16, not in the source issue's original 3 tiers.** These 15 hardcode a
      non-default disk type instead of falling through the `${BOOT_DISK_TYPE:-pd-balanced}` pattern the rest of the
      corpus uses: `launch-aave-lending-rate-validation-vm.sh`, `launch-funding-ensemble-paper-cron-vm.sh`,
      `launch-client-reporting-cutover-vm.sh`, `launch-amm-golden-fixture-validation-vm.sh`,
      `launch-dr-drill-cutover-vm.sh`, `launch-strategy-live-vm.sh`, `launch-defi-backtest-vm.sh`,
      `launch-defi-paper-trading-vm.sh`, `launch-defi-recursive-borrow-vm.sh`, `launch-execution-alpha-vm.sh`,
      `launch-disaster-drill-cron-vm.sh`, `launch-strategy-paper-vm.sh`, `launch-strategy-backtest-grid-vm.sh`,
      `launch-wallet-treasury-cutover-vm.sh` (all `pd-ssd`), and `launch-planning-vm.sh` (`pd-standard` — the
      orchestrator VM itself). `lc_gcloud_create` never passes `--boot-disk-type` at all (confirmed 0 grep hits in
      `launcher_common.sh`), so migrating any of these 15 as-is silently regresses them to GCE's bare default
      (pd-balanced) — most are live-trading/strategy/execution/DR-cutover VMs where a deliberate IOPS choice (pd-ssd)
      or cost choice (pd-standard on the orchestrator) is plausible, not an artifact. One of the 15
      (`launch-funding-ensemble-paper-cron-vm.sh`) is ALSO currently listed in the "Migrate group B" todo below as
      directly-migratable — flagged directly to that task's owner (slot 17) via `/api/slots/17/message`, not resolved
      here. Options: (a) add an optional `boot_disk_type` param to `lc_gcloud_create` (backward compatible — omit it,
      unchanged pd-balanced-default behavior for the ~124 non-override callers) so all 15 can migrate without losing
      their disk type; (b) carve these 15 out of this migration's scope permanently (document why in
      `vm-launcher-runbook.md`'s Known Issues, same as a SPOT/metadata-from-file carve-out would be documented).
      **Done when**: the operator states a decision (a/b) in this todo's own reply or the Progress Log below, same
      closure mechanism as todos 1/2. Repo: unified-trading-pm (decision only — no code in this todo). Source: this
      plan's own `--boot-disk-type` review (2026-08-16, slot 12).
      **DECIDED 2026-08-18: option (a) — add the optional `boot_disk_type` param.**


- [ ] [SCRIPT] P2. Implement the `boot_disk_type` param decided above (backward compatible), migrate the 15 named
      launchers to use it instead of hardcoding `--boot-disk-type`. Cross-check the one already flagged to slot 17's
      "Migrate group B" task before touching it. Repo: unified-trading-pm.

- [x] ✅ [OPERATOR] P2. **DONE 2026-08-19 (`/plan-reconcile security_and_cross_cutting_master` Phase 2 flip — same
      class as the todo above: done-when already satisfied by the DECIDED line below, checkbox never flipped).**
      **Resolve two more genuine blocking gaps found during group B's migration (2026-08-16, slot 17) —
      neither in this plan's or the source issue's original tier list.** (1) **`;`-delimited-metadata callers**
      (`launch-manifest-recon-all-vm.sh`, `launch-manifest-recon-apply-vm.sh` confirmed so far — likely others in group
      C given the same `VENUES=`-can-contain-commas pattern): `lc_gcloud_create`'s internal guards
      (`lc_verify_setup_script_freshness`, the canonicalisation-gate lookup) both use `grep -oE '[^|,]+'` to extract a
      value from `metadata_str`, which only terminates at `,`/`|` — a caller using the `^;^...;...` gcloud
      custom-delimiter form (no commas at all) makes both regexes capture to end-of-string, silently degrading both
      guards to a no-op warn (traced: non-fatal, but the exact protection this whole migration effort exists to add
      goes silently missing for these launchers). (2) **`--accelerator` (GPU) callers**
      (`launch-ml-training-vm.sh`, `launch-ml-vm.sh`): `lc_gcloud_create`'s fixed 8-positional signature has no
      accelerator parameter at all — migrating would silently drop GPU provisioning for any `--machine gpu` invocation.
      Options: (a) fix `lc_verify_setup_script_freshness`/canonicalisation-gate's regexes to also stop at `;` (a small,
      low-risk change — `[^|,;]+` — since no legitimate metadata value should contain a literal semicolon either) +
      add an optional 9th `accelerator` positional (or a metadata-embedded convention) to `lc_gcloud_create`, then
      migrate the 4 held-back launchers; (b) carve GPU-capable and `;`-delimited-metadata launchers out of this
      migration's scope permanently (document both in `vm-launcher-runbook.md`'s Known Issues, same as the SPOT
      carve-out would be). **Done when**: the operator states a decision (a/b) in this todo's own reply or the Progress
      Log below, same closure mechanism as todos 1/2. Repo: unified-trading-pm (decision only — no code in this todo).
      Source: this plan's own group-B migration (2026-08-16, slot 17).
      **DECIDED 2026-08-18: option (a) — fix the regexes to stop at `;` and add accelerator passthrough.**

- [ ] [SCRIPT] P2. Implement the semicolon-regex fix (`[^|,]+` → `[^|,;]+`) + accelerator passthrough decided above,
      migrate `launch-manifest-recon-all-vm.sh`, `launch-manifest-recon-apply-vm.sh`, `launch-ml-training-vm.sh`,
      `launch-ml-vm.sh`, and any other group-C launchers sharing the pattern. Repo: unified-trading-pm.

- [ ] [DOCS] P3. **Correct the source issue doc's stale "large disk / `${BOOT_DISK_SIZE%GB}` extraction" tier (1) —
      measured 0/149 launchers use that pattern.** `lc_gcloud_create`'s `disk_gb` (positional arg 5) is already a plain
      numeric value with no `GB` suffix to strip — a caller passing `"${BOOT_DISK_SIZE:-250GB}"` style would need to
      strip the suffix before calling the wrapper, but `grep -l 'BOOT_DISK_SIZE%GB' scripts/vm/*.sh` returns 0 hits
      fleet-wide, so no launcher actually does this today and none needs to going forward — this "complexity tier" from
      the source issue's 2026-07-31 framing does not correspond to any real file. Edit
      `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s follow-up todo text to drop tier (1) and note it was
      re-measured away 2026-08-16 (do not delete the historical record — strike through or annotate, per the "fix stale
      pointers in place" rule). **Done when**: the source issue doc no longer states tier (1) as live open work. Repo:
      unified-trading-pm.

- [x] ✅ [SCRIPT] P2. **Migrate group A (14 of the listed 15 launchers) to `lc_gcloud_create` — no SPOT/metadata-from-file
      blockers, safe to migrate under the CURRENT wrapper signature.** Migrated (all in `deployment-service/scripts/vm/`):
      `launch-aster-forward-poll.sh`, `launch-batch-live-recon-cron-vm.sh`, `launch-blank-reason-recon-vm.sh`,
      `launch-bucket-rsync-vm.sh`, `launch-cefi-forward-poll.sh`, `launch-cefi-migration-vm.sh`,
      `launch-cefi-mvp-reclassify-vm.sh`, `launch-cefi-onchain-forward-poll.sh`,
      `launch-defi-forward-poll.sh`, `launch-defi-manifest-force-consolidate-vm.sh`,
      `launch-defi-pool-instrument-type-restamp-vm.sh`, `launch-features-cross-cutting.sh`,
      `launch-fill-missing-player-stats-vm.sh`, `launch-fixtures-recovery-vm.sh`. **`launch-dashboard-vm.sh` EXCLUDED —
      finding, not a skip**: it calls `gcloud compute instances create-with-container` (container-based deploy, with
      `--container-image`/`--container-env`/`--container-restart-policy`/`--tags`), a different gcloud subcommand
      `lc_gcloud_create` cannot express at all (the wrapper only issues `gcloud compute instances create`). It only
      matched this todo's `grep -l "gcloud compute instances create"` corpus scan as a SUBSTRING false-positive
      (`create-with-container` contains the literal string `create`) — not a genuine raw-create launcher, so the
      corpus's "149 raw-create launchers" / "45 directly migratable" counts in this plan's summary/table are each off
      by one (148 / 44 real raw-`instances create` callers). Migrating it would need a new
      `lc_gcloud_create_with_container` wrapper (out of scope for this todo — flagging for a future todo if a
      container-VM launcher guard is wanted). Each migrated file replaced its raw `gcloud compute instances create`
      block with `lc_gcloud_create "$VM_NAME" "$PROJECT" "$ZONE" "$MACHINE_TYPE" "$DISK_GB" "$METADATA_STR"
      "$LABELS_STR" "$SERVICE_ACCOUNT"`, mirroring `deployment-service@6998cc228`'s pattern (`! DRY_RUN` →
      `export LC_DRY_RUN` gating, dropped the now-redundant manual `managed-by=deployment-service` label and the
      unsupported `--boot-disk-type` flag). Also fixed a duplicated `lc_verify_tarball_freshness` block in
      `launch-aster-forward-poll.sh` and a stale dry-run echo string in `launch-defi-forward-poll.sh`.
      **Done**: `grep -L lc_gcloud_create <14 files>` returns empty; `bash -n` clean on all 14; `--dry-run`/
      `LC_DRY_RUN=true` smoke on 3 sampled launchers (aster-forward-poll, cefi-forward-poll, blank-reason-recon)
      confirmed unchanged VM name/metadata/labels/service-account; `quality-gates.sh` green (270s). Shipped
      — deployment-service@e766d26445. Repo: deployment-service.

- [x] ✅ [SCRIPT] P2. **Migrate group B (10 of the listed 15 launchers) to `lc_gcloud_create` — 5 EXCLUDED, findings not
      skips.** Migrated (all in `deployment-service/scripts/vm/`): `launch-fixtures-truthset-audit-vm.sh`,
      `launch-gcs-migration-phase0-calibration.sh`, `launch-kalshi-bulk-seed-vm.sh`, `launch-mdps-features-live.sh`,
      `launch-mdps-odds-horizon-bucket-restamp-vm.sh`, `launch-measure-honest-coverage-vm.sh`,
      `launch-mtds-gas-fees-fleet-vm.sh`, `launch-mtds-live-cefi-consolidated.sh`,
      `launch-mtds-live-prediction-consolidated.sh`, `launch-mtds-live.sh`. Each replaced its raw
      `gcloud compute instances create` block with `lc_gcloud_create "$VM_NAME" "$PROJECT" "$ZONE" "$MACHINE_TYPE"
      "$DISK_GB" "$METADATA_STR" "$LABELS_STR" "$SERVICE_ACCOUNT"`, mirroring `deployment-service@6998cc228`'s pattern
      (`! DRY_RUN` → `export LC_DRY_RUN` gating, dropped the now-redundant manual `managed-by=deployment-service` label
      and the unsupported `--boot-disk-type` flag — all 10 already defaulted to `${BOOT_DISK_TYPE:-pd-balanced}`, so
      dropping it is a no-op per the review todo above's finding, not a regression).
      **5 EXCLUDED — 3 genuinely new blocking gaps found, none in this plan's or the source issue's tier list**:
      - `launch-manifest-recon-all-vm.sh` / `launch-manifest-recon-apply-vm.sh`: both build a `;`-delimited
        `metadata_str` (the `^;^startup-script-url=...;VM_TASK=...` gcloud custom-delimiter form — required because
        their `VENUES=` value can itself contain commas). `lc_gcloud_create`'s own internal guards —
        `lc_verify_setup_script_freshness`'s `grep -oE 'startup-script-url=gs://[^|,]+'` and the canonicalisation-gate's
        `grep -oE 'VM_ASSET_GROUP=[^|,]+'` — only ever stop at `,` or `|`. With no comma anywhere in a `;`-delimited
        string, both regexes greedily capture to end-of-string instead of just the URL / asset-group value. Traced the
        downstream effect (read `lc_verify_setup_script_freshness` + `lc_verify_canonicalisation_gate` in
        `launcher_common.sh`): non-fatal in default mode (both guards degrade to a silent no-op warning rather than
        blocking the launch — `local_path` doesn't exist → freshness check skips; the canonicalisation-gate marker
        lookup 404s → warn-mode passes), so the VM would still launch correctly, but the exact protection this whole
        migration exists to add would be silently absent for these 2 launchers specifically. Migrating them today would
        make the checkbox lie about what's actually protected.
      - `launch-ml-training-vm.sh` / `launch-ml-vm.sh`: both support `--machine gpu`, which sets
        `ACCELERATOR="--accelerator=type=nvidia-tesla-t4,count=1"` on the `gcloud compute instances create` call.
        `lc_gcloud_create`'s fixed 8-positional-arg signature (`launcher_common.sh:528-611`, re-confirmed via `grep -n
        accelerator launcher_common.sh` → 0 hits) has no accelerator parameter and no passthrough mechanism — migrating
        would silently drop GPU provisioning for any `--machine gpu` invocation (misconfigured VM, not a launch
        failure, so it would go unnoticed until a training run either fails on missing CUDA or silently runs CPU-only).
      - `launch-funding-ensemble-paper-cron-vm.sh`: hardcodes `--boot-disk-type=pd-ssd` unconditionally (no env/CLI
        override) — independently found here, then confirmed already flagged by the review todo above's 2026-08-16
        pd-ssd/pd-standard-tier finding (which separately pinged this task). `lc_gcloud_create` never sets
        `--boot-disk-type` at all, so migrating would silently downgrade this launcher from its deliberate pd-ssd
        choice to GCE's bare default.
      **Done (for the 10 migrated)**: `grep -L lc_gcloud_create <10 files>` returns empty; `bash -n` clean on all 15
      group-B files (10 migrated + 5 untouched); `--dry-run` smoke on 2 sampled launchers (`launch-fixtures-truthset-
      audit-vm.sh`, `launch-mtds-live.sh`) confirmed unchanged VM name/metadata/labels/service-account;
      `quality-gates.sh` green (439s). Shipped — deployment-service@21368ca7af (rebased once onto a concurrent
      landing before push; QG re-verified green on the rebased SHA — post-push ancestry independently confirmed).
      The 5 excluded files are unmodified,
      still raw-`gcloud compute instances create` — carried forward as a new `[OPERATOR]` todo below (accelerator +
      delimiter gaps) plus the existing pd-ssd/pd-standard todo (which already covers the 3rd file). Repo:
      deployment-service.

- [x] ✅ [SCRIPT] P2. **Migrate group C (14 of the listed 15 launchers) to `lc_gcloud_create` — 1 EXCLUDED, finding not
      skip.** Migrated (all in `deployment-service/scripts/vm/`): `launch-perp-clob-live.sh`,
      `launch-perp-funding-manifest-restamp-vm.sh`, `launch-prediction-forward-poll.sh`, `launch-prediction-live.sh`,
      `launch-replay-cascade.sh`, `launch-sfi-forward-poll.sh`, `launch-sport-residue-blank-venue-purge-vm.sh`,
      `launch-sports-ensemble-train-vm.sh`, `launch-sports-full-sweep-vm.sh`, `launch-tradfi-forward-poll.sh`,
      `launch-tradfi-session-stamp-vm.sh`, `launch-tradfi-session-stamps-vm.sh`, `launch-transfermarkt-forward-poll.sh`,
      `launch-understat-forward-poll.sh`. **`launch-rate-calibration-probe-vm.sh` EXCLUDED — finding, not a skip**: it
      passes `--no-address` (no public IP, deliberate hardening for this throwaway probe VM) — `lc_gcloud_create` has
      zero support for that flag (confirmed reading its fixed flag set in `launcher_common.sh:528-611`: `--project`,
      `--zone`, `--machine-type`, `--image-family`, `--image-project`, `--boot-disk-size`, `--scopes=cloud-platform`,
      `--no-restart-on-failure`, optional `--service-account`, `--metadata`, `--labels` — no `--no-address` and no
      passthrough mechanism), so migrating it would silently give the VM a public IP it never had. Same shape as
      group A's `launch-dashboard-vm.sh` exclusion (a flag/verb the wrapper cannot express) — flagging for a future
      todo if a `--no-address` param is wanted, not a new `[OPERATOR]` todo (a narrow single-file additive gap, not a
      genuine design fork). Each migrated file replaced its raw `gcloud compute instances create` block with
      `lc_gcloud_create <vm_name> <project> <zone> <machine_type> <disk_gb> <metadata_str> <labels_str>
      <service_account>`, mirroring the group A/B pattern (`! DRY_RUN` → `export LC_DRY_RUN` gating on the launchers
      whose own dry-run semantics actually skip VM creation; dropped the unsupported `--boot-disk-type` flag and the
      now-redundant manual `managed-by=deployment-service` label).
      **New finding, not previously documented in this plan or the source issue**: `launch-tradfi-session-stamp-vm.sh`'s
      own `--dry-run` flag only ever dry-runs the *internal* migration script it launches
      (`migrate_tradfi_ohlcv_session_stamps.py --dry-run`) — it never gated the actual VM-creation call, so
      `--dry-run` on this launcher has ALWAYS created a real VM (a pre-existing bug, not introduced by this
      migration; confirmed live by accidentally launching a real VM during my own `--dry-run` smoke test, see
      Progress Log). Migrated its create call unconditionally (unchanged observable behavior) rather than silently
      "fixing" it mid-migration; filed a dedicated follow-up todo below per operator instruction instead. Checked
      sibling `launch-tradfi-session-stamps-vm.sh` for the same defect — NOT affected (no `--dry-run` flag exists
      there at all; its dry/full mode is a bare positional arg).
      **Done (for the 14 migrated)**: `bash -n` clean on all 14; `grep -L lc_gcloud_create <14 files>` returns empty;
      `--dry-run` smoke on 2 sampled launchers (`launch-perp-clob-live.sh`, `launch-sfi-forward-poll.sh`) confirmed
      unchanged VM name/metadata/labels/service-account; `quality-gates.sh` green (re-verified after 2 concurrent
      rebases from sustained branch churn). Shipped — deployment-service@1794ecd1fe (rebased twice onto concurrent
      landings before push; QG re-verified green on each rebased SHA; post-push ancestry independently confirmed).
      The excluded file is unmodified, still raw-`gcloud compute instances create` — carried forward as a note above,
      not a new `[OPERATOR]` todo. Repo: deployment-service.

- [ ] [SCRIPT] P3. **Fix `launch-tradfi-session-stamp-vm.sh`'s `--dry-run` flag so it actually skips VM creation** —
      found during group C's migration (2026-08-16, slot 18): the flag has ALWAYS only dry-run the *internal*
      `migrate_tradfi_ohlcv_session_stamps.py` script, never gated the VM-creation call itself, so `--dry-run`
      silently launches a real GCE VM (confirmed live — slot 18's own `--dry-run` smoke test accidentally created
      `canonical-migration-tradfi-sessionstamp-20260816-031642`, RUNNING; operator-ruled leave-it-to-self-shutdown
      per `BLK-27fa36df` rather than force-delete under the `canonical-migration-` prefix delete guardrail, rather
      than delete it). Fix: mirror the other Pattern-1 launchers in this batch — gate the `lc_gcloud_create` call on
      `[[ "${DRY_RUN:-false}" != "true" ]]` (or an early `exit 0` before it, matching the Pattern-A restamp/purge
      launchers), so `--dry-run` prints the plan and exits without creating a VM. Sibling `launch-tradfi-session-
      stamps-vm.sh` was checked and does NOT have this defect (no `--dry-run` flag at all). **Done when**:
      `bash launch-tradfi-session-stamp-vm.sh --dry-run ...` prints a dry-run plan and does not create a real VM
      (verify via `gcloud compute instances list --filter="name~^canonical-migration-tradfi-sessionstamp-"` showing
      no new instance after the dry-run call). Repo: deployment-service.

- [ ] [INFRA] P3. **Update `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s follow-up todo + this plan's own
      Progress Log once groups A/B/C ship and todos 1-3 are ruled**, recording: the corrected 149-launcher baseline, the
      45-launcher direct-migration completion, and either the follow-up batch reference (if SPOT/metadata-from-file
      migration work gets drafted next) or the carve-out rationale (if the operator ruled to exclude either tier). If
      every todo above reaches a terminal state and no further work is gated here, propose this plan for archival per
      the 6-step ritual. Repo: unified-trading-pm.

## Deferred

The SPOT-tier (79 launchers), metadata-from-file-tier (47 launchers), and pd-ssd/pd-standard-tier (15 launchers,
found during the 2026-08-16 `--boot-disk-type` review) migrations are **not** drafted as todos here — each is blocked
on its own `[OPERATOR]` ruling above (todos 1/2, and the new pd-ssd/pd-standard todo). Once any rules, the actual
per-launcher migration for that tier should be drafted as a follow-up `infra_satellite_ao_dispatch_batch18+` plan (or
folded into this one via edit, operator's call), sized the same way as groups A/B/C (disjoint ~15-file todos). Drafting
them now, before the wrapper even supports the flags they need, would produce todos with no achievable done-when —
exactly what this plan's own rules section says to avoid.

## Progress Log

- **infra 2026-08-16 (slot 9)**: authored. Re-measured the raw-create corpus fresh (149, not ~136) and `lc_gcloud_create`'s
  actual signature against it — found the SPOT-provisioning gap (79 launchers, undocumented in the source issue) and
  confirmed the source issue's "large disk" tier does not correspond to any real file (0/149). Drafted 3 disjoint
  15-file migration todos for the 45 launchers with no blocking gap, plus 3 OPERATOR/REVIEW todos for the genuinely open
  forks — none resolved unilaterally, per the source todo's own 2026-08-12 ao-readiness clarification.
- **review 2026-08-16 (slot 12)**: resolved the `--boot-disk-type` review todo. Ran the full corpus instead of a
  15-file sample (cheap: `grep -h boot-disk-type scripts/vm/*.sh | sort | uniq -c`) — confirmed ~124 launchers
  genuinely default to `pd-balanced` with zero external override anywhere in the repo (approved "document sufficient"
  for those), but found a genuine-override tier the original todo's 2-file spot-check missed: **15 launchers hardcode
  a non-default disk type** (14 × `pd-ssd`, 1 × `pd-standard`), and `lc_gcloud_create` never passes `--boot-disk-type`
  at all, so migrating any of the 15 as-is would silently regress their disk type. Filed a new `[OPERATOR]` todo for
  that tier (mirrors todos 1/2's pattern) and updated `## Deferred`. Found + handled a live conflict: one of the 15,
  `launch-funding-ensemble-paper-cron-vm.sh`, was already in the dispatched "Migrate group B" task's file list —
  pinged slot 17 (Group B's owner) directly via `/api/slots/17/message` to exclude it, rather than editing their
  live-dispatched todo out from under them.
- **infra 2026-08-16 (slot 16)**: shipped group A — 14 of the listed 15 files migrated to `lc_gcloud_create`
  (deployment-service@e766d26445), QG green. Found `launch-dashboard-vm.sh` is not actually a raw-create launcher —
  it calls `gcloud compute instances create-with-container`, a distinct gcloud subcommand the wrapper can't express;
  it only matched the corpus's `grep -l "gcloud compute instances create"` scan as a substring false-positive. Left
  it unmigrated (see the flipped checkbox above for the full finding) — this means the plan summary's "149
  raw-create" / "45 directly migratable" corpus counts are each off by one real file (148 / 44). Did not correct the
  summary/table numbers here since that risks racing group B/C's own in-flight edits to the same doc; flagging for
  whoever runs todo "Update follow-up + Progress Log" (or a future corpus re-measurement) to fold in.
- **infra 2026-08-16 (slot 17)**: shipped group B — 10 of the listed 15 files migrated to `lc_gcloud_create`
  (deployment-service@21368ca7af), QG green (439s), `--dry-run` smoke-verified on 2 sampled launchers. Held back 5:
  `launch-funding-ensemble-paper-cron-vm.sh` (independently re-confirmed the review todo's pd-ssd finding — already
  flagged there, no new todo needed for it), plus 2 newly-found gaps not previously documented anywhere in this plan
  or the source issue — `launch-manifest-recon-all-vm.sh`/`-apply-vm.sh` (their `;`-delimited metadata_str silently
  defeats `lc_gcloud_create`'s internal freshness/canonicalisation-gate guards via a `[^|,]+` regex that doesn't stop
  at `;`) and `launch-ml-training-vm.sh`/`launch-ml-vm.sh` (their `--machine gpu` path needs `--accelerator=...`,
  which the wrapper's fixed positional signature has no way to express). Filed a new `[OPERATOR]` todo for both new
  gaps rather than silently migrating past them or absorbing a wrapper-code fix into this already-dispatched todo's
  scope.
- **infra 2026-08-16 (slot 18)**: shipped group C — 14 of the listed 15 files migrated to `lc_gcloud_create`
  (deployment-service@1794ecd1fe), QG green, `--dry-run` smoke-verified on 2 sampled launchers. Held back
  `launch-rate-calibration-probe-vm.sh` — its `--no-address` flag has zero equivalent on `lc_gcloud_create`, a
  narrow previously-undocumented additive gap, not a design fork (see the flipped checkbox above). Found a
  pre-existing bug while smoke-testing: `launch-tradfi-session-stamp-vm.sh`'s `--dry-run` never actually skipped VM
  creation — it accidentally launched a real VM (`canonical-migration-tradfi-sessionstamp-20260816-031642`) during
  my own smoke test. Operator ruled (`BLK-27fa36df`) to leave it — it runs the migration script in `--dry-run`
  (read-only) mode with `VM_SHUTDOWN_ON_COMPLETION=true`, so it self-terminates harmlessly; this VM is EXPLAINED,
  not a mystery VM for the fleet watchdog. Filed a dedicated follow-up `[SCRIPT]` todo above for the fix (checked
  sibling `launch-tradfi-session-stamps-vm.sh` for the same defect — not affected, no `--dry-run` flag exists
  there). Also: `live-defi-rollout` was under sustained push churn during this ship — quickmerge rebased my commit
  twice (274b858c → 575c0b28 → 1794ecd1fe), each requiring a fresh QG pass before the next push attempt; final SHA
  independently verified as an ancestor of `origin/live-defi-rollout`.
- **data_engineering 2026-08-16 (slot 26)**: shipped todo 1 — added optional
  `provisioning_model`/`instance_termination_action` params to `lc_gcloud_create` per the operator's option-(a) ruling
  (deployment-service@274233a891, `test_vm_launcher_scripts.py` full suite 246 passed, `quality-gates.sh` green
  245s). Verified both bundled requirements rather than just asserting them: preemption-recovery resume-from-PROGRESS
  is unaffected (traced `RelaunchPreemptedVm`'s replay path — independent of this wrapper), and the
  idempotent-skip-existing-without-`--force` contract holds under the new SPOT-enabled call shape (2 new regression
  tests: refuses a duplicate against a RUNNING shard, permits relaunch once no longer RUNNING). Updated
  `vm-launcher-runbook.md`'s Known Issues with what shipped + what was verified. This unblocks (but does not itself
  perform) the 79-launcher SPOT-tier migration, which is still deferred to a follow-up batch per `## Deferred` above.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
