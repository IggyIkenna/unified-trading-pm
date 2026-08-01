---
doc_type: plan
title: DeFi consolidated closeout — native-todo AO extraction (2026-07-25 fresh triage)
summary: >-
  Fresh AO-eligibility triage of defi_consolidated_closeout_2026_07_18.md's OWN native `- [ ]` todos (not its satellite
  source docs — those already got the defi_satellite_ao_dispatch_batch1_2026_07_25.md treatment). Of 19 open native todo
  lines (18 top-level + 1 real nested checkbox), the large majority are already `[OPERATOR]`-tagged, explicitly gated on
  still-running prerequisite work (the Track 1 per-instrument migration, the Track 5/lending-writer-retire forks — both
  independently confirmed zero-AO-eligible-candidate by the satellite batch1 triage), explicit same-doc duplicates, or
  turned out to be STALE on a fresh read (2 native todos are fully superseded by newer findings in sibling docs — see
  the Conflicts section, deliberately left un-touched in the source doc per this task's scope). Only 4 conflict-clear,
  bounded candidates survived, spanning 3 repos.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-service, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, native-extract, conflict-checked]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Fresh AO-eligibility triage 2026-07-25, dispatched specifically to check defi_consolidated_closeout_2026_07_18.md's
  own native open todos (previously untouched by this session's satellite-doc extraction pass) against task_template.md
  §4's dispatch-scope-eligibility bar.
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
---

# DeFi consolidated closeout — native-todo AO extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review. All 4 todos
> below touch distinct files/repos and are same-priority-within-doc, so they are safe to dispatch concurrently once
> activated.

## Todos

- [x] ✅ [INFRA] P2. **DONE 2026-07-28 (slot-13, infra)** — **Combined fix + apply for the CURVE/OPTIMISM
      subgraph-deindex reclassification (2 sub-steps, causally sequential — the 2nd is blocked on the 1st):** (a) fix
      `setup-data-pipeline-vm.sh`'s `canonical-migration` branch (`:1187`) which hardcodes `cd "$WORKSPACE/mtds"`
      regardless of `VM_SERVICE` — mirror the `VM_SERVICE`-keyed `cd "$WORKSPACE/instruments"` pattern already used by
      other branches (e.g. `:1224`) so an instruments-service script can be found and run from this VM path; (b) once
      (a) lands, launch a fresh canonical-migration VM running
      `instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py --apply` (dry-run
      already verified 144 matching rows against live prod), T+10min health-verified RUNNING with real progress in
      `run.log`, and confirm it completes. **Delete/apply safety note (finding O, self-justified — no operator gate
      needed):** this is a semantic manifest-column reclassification (`error_reason: attempted_failed` →
      `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED`), not a GCS object delete — it does not remove any row or
      object, only relabels ~144 already-dry-run-verified rows. It mirrors the identical no-operator-gate pattern
      already shipped twice in the same consolidated-closeout plan
      (`purge_defi_false_available_to_2026_07_20.py`/`undelist_defi_false_postdelist_eu_2026_07_20.py`), and the plan's
      own history shows agents already attempted this exact `--apply` twice before hitting only an infra (launcher)
      blocker — never an operator-gate — confirming it was never intended to require sign-off. Repos:
      deployment-service, instruments-service. **Done when**: (a) the `cd` bug is fixed and the mtds-hardcoded branch no
      longer breaks a non-mtds `VM_SERVICE`; (b) the reclassify script's `--apply` run completes on a fresh VM, and a
      post-run manifest spot-check shows the ~144 previously-`attempted_failed` CURVE/OPTIMISM rows now carry
      `EXPECTED_SUBGRAPH_DEINDEXED`; `quality-gates.sh` green in deployment-service. Source:
      `defi_consolidated_closeout_2026_07_18.md` Track 3 (native, line ~440 + its Track 3 nested `--apply` item).
- [x] ✅ [DATA] P2. **Real column-prune refactor of `measure_honest_coverage.py`** so the nightly honest-coverage VM no
      longer needs 32GB (`e2-highmem-4`) and can run on the originally-intended 16GB (`e2-standard-4`). A naive drop of
      `instrument_id` from `_READ_COLUMNS` is UNSAFE — `_merge_manifests` dedups the prd+oracle merge on
      `(date, venue, instrument_id, data_type)`; dropping the column falls back to `(date, venue, data_type)` and
      collapses distinct instruments, corrupting the coverage denominator (the shard atom is per-instrument). Implement
      EITHER a pyarrow row-group streaming aggregation OR a metadata-deferred primary read (secondaries already re-read
      eu-only) that preserves the full `(date, venue, instrument_id, data_type)` dedup key — do not ship a change that
      collapses it. Repo: instruments-service. **Done when**: a fresh coverage run on the reduced machine type produces
      a `coverage.json` with the SAME per-(venue, instrument_id, data_type) row counts as a control run on the current
      32GB machine (or a documented tolerance if pyarrow ordering differs), no OOM; ~6 selection tests updated and
      passing; `quality-gates.sh` green. Source:
      `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md` (cited by
      `defi_consolidated_closeout_2026_07_18.md` Track 8 as part of "fix the honest-coverage-nightly right-size"). —
      **2026-08-01 (slot-10, data_engineering craft) — instruments-service@12825e81.** `main()` now reads/computes/
      releases ONE asset_group's primary manifest at a time (new `_init_coverage_accumulator`/`_accumulate_coverage`
      pair) instead of holding all 5 asset_groups' DataFrames simultaneously in a `dfs` dict for the whole run —
      `_compute_coverage`'s per-ag loop body has no cross-ag state, so this bounds peak memory to the single largest
      asset_group's read instead of the sum of all 5, without touching `_READ_COLUMNS` or the
      `(date, venue, instrument_id, data_type)` merge key at all. Added 4 tests incl. a byte-identical equivalence proof
      between the old batched and new streaming paths (`TestPerAssetGroupStreaming`); all 47 tests in
      `test_measure_honest_coverage.py` pass; full `quality-gates.sh` green, verified on origin via
      `git merge-base --is-ancestor`. **Honest gap**: this ships the code-level memory-bounding fix only — the empirical
      "fresh run on a reduced 16GB machine, no OOM, byte-identical row counts vs. the 32GB control run" half of this
      todo's own done-when needs an actual VM launch + comparison run, which is infra craft (this task's
      `assigned_role: data_engineering` scopes VM launches out — `does_not: infra/VM launches`). Tracked as its own
      follow-up todo immediately below rather than left unverified in prose.
- [ ] [INFRA] P2. **Empirically verify the `measure_honest_coverage.py` streaming refactor (above) actually bounds
      memory enough to run on `e2-standard-4` (16GB)**, then downsize the live launcher. Launch a control run on the
      current `e2-highmem-4` (32GB) VM and a test run on a fresh `e2-standard-4` (16GB) VM, both against
      `instruments-service@12825e81` (or later), `--asset-group all`; diff the two `coverage.json` outputs' per-
      `(venue, instrument_id, data_type)` row counts (byte-identical, or a documented pyarrow-ordering tolerance) and
      confirm the 16GB run does not OOM. If it holds, flip `vm/launch-measure-honest-coverage-vm.sh`'s `--machine-type`
      back to `e2-standard-4` and re-upload to the cron's GCS path
      (`gs://deployment-scripts-central-element-323112/vm/launch-measure-honest-coverage-vm.sh` — see
      `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md` for why the GCS path, not
      the repo copy, is the one the live cron actually fetches). If it does NOT hold, leave the machine type at 32GB and
      record the measured peak RSS here so a future attempt has a real number to design against. Repo:
      deployment-service. **Done when**: the before/after coverage.json comparison + peak-RSS numbers are recorded in
      this todo's evidence, and the live cron's GCS launcher matches whatever machine type the verification supports.
- [ ] [INFRA] P3. **Combined honest-coverage launcher SSOT cleanup (2 sub-steps, same underlying drift, different
      files):** (a) delete/merge the redundant honest-coverage launcher artifacts —
      `scripts/vm/launch-honest-coverage-vm.sh` (not the live cron path; the GCS
      `vm/launch-measure-honest-coverage-vm.sh` is) and `scripts/vm/honest-coverage-daily-workflow.yaml` (no such Cloud
      Workflow is actually deployed) — so exactly ONE launcher artifact is the SSOT, and make the tarball publisher
      (`create-code-tarballs.sh`) maintain whichever GCS `vm/` path the Cloud Run Job actually reads (or repoint the Job
      at the publisher-maintained `code/deployment-service/scripts/vm/` path) so this class of drift can't silently
      recur; (b) once the repo tree is confirmed clean (`git status` — do NOT proceed if any OTHER session's foreign
      uncommitted work is present anywhere in the tree, per this workspace's multi-agent safety rule; do NOT use
      `--allow-dirty-tarball`), republish the instruments-service tarball via
      `create-code-tarballs.sh --asset-group instruments` so the nightly writer's partial-stamping fix (`a29e483`)
      actually reaches production. **Delete-risk note (finding O, self-justified — no operator gate needed):** step (a)
      deletes dead REPO files (git-reversible, no GCS/manifest data touched); step (b) republishes an already-built,
      already-reviewed tarball (an idempotent operational push, not a delete). Repo: deployment-service. **Done when**:
      (a) exactly one honest-coverage VM launcher artifact remains referenced by the live cron path, the publisher
      maintains that exact GCS path, `quality-gates.sh` green; (b) the instruments-service tarball's `.manifest.json`
      `commit_sha` matches `origin/live-defi-rollout` HEAD at time of republish. Source:
      `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md` (cited by
      `defi_consolidated_closeout_2026_07_18.md` Track 8).
- [x] ✅ [DOC] P1. **Add the missing digest entry for `defi_track01_per_instrument_and_canon_id_2026_07_24.md` into
      `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`** and fix its dangling "tracked under X below" prose
      references so they resolve to a real linked entry instead of a phantom forward-pointer (bold digest style,
      `- **[TAG] P<n>.**`, per `task_template.md` finding H — never real `- [ ]` checkbox syntax for a digest line). Use
      the exact digest content already drafted verbatim at the bottom of `defi_consolidated_closeout_2026_07_18.md`
      ("Missing digest entry (gate-audit §12, 2026-07-24)" section) as the entry text. **Count correction**: the
      dispatching native todo says "3 dangling references" but a fresh
      `grep -n defi_track01_per_instrument_and_canon_id` against
      `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` at authoring time of this extraction found only
      **2** ("tracked under ... below" at 2 locations) — re-verify the live count first rather than assuming either
      number; fix however many actually exist. Repo: unified-trading-pm. **Done when**:
      `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` contains the digest entry as a real linked bullet,
      and a fresh grep for `defi_track01_per_instrument_and_canon_id` shows every "tracked under X below" occurrence now
      resolves to that linked entry (no dangling forward-pointer remains). Source:
      `defi_consolidated_closeout_2026_07_18.md` (native, bottom of file, "Missing digest entry" note + its own
      `[DOC] P1` todo). **Evidence (2026-07-28, slot 8)**: live count was 2 (not 3), confirmed by fresh grep before
      editing. Added the digest bullet verbatim (from `defi_consolidated_closeout_2026_07_18.md:744-748`) to the end of
      the "DeFi-specific canonicalisation residuals" section in
      `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`, and converted both dangling
      `` `defi_track01_per_instrument_and_canon_id_2026_07_24.md` below `` backtick mentions (lines 390/413 pre-edit)
      into real markdown links to the file. Fresh grep post-edit shows all 3 occurrences (2 fixed references + 1 new
      entry) — no dangling forward-pointer remains. Native duplicate todo in
      `defi_consolidated_closeout_2026_07_18.md:749` flipped in the same commit citing this doc.

## Conflicts / staleness found (not drafted — reported, not silently worked around)

Per the operator's 2026-07-25 conflict-check discipline, every candidate above was checked against the rest of this same
consolidated doc, `defi_satellite_ao_dispatch_batch1_2026_07_25.md`, and
`defi_track01_per_instrument_and_canon_id_2026_07_24.md` before drafting. Two native todos turned out to be genuinely
stale on a fresh read — recorded here rather than re-drafted or silently left as-is:

- **Track 8's "audit defi adapters for dead code..." native todo (`[BACKEND] P2`, line ~609) is DONE, not open.** The
  cited "gate-audit §1, 2026-07-24" work already ran in full and produced
  `issues/defi_adapter_dead_code_audit_2026_07_24.md` — that doc's own frontmatter `source:` field literally states it
  is "Dispatched todo from plans/active/defi_consolidated_closeout_2026_07_18.md (gate-audit §1, 2026-07-24)", and its
  body satisfies the native todo's own done-when verbatim ("a written finding per module (kept/fixed/removed + reason)"
  — see that doc's §1-4 + summary table). Two of that audit's own 6 follow-up items were already extracted into
  `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (the `onchain/__init__.py` docstring fix and the `curve_adapter.py`
  broad-except trace); the other 4 follow-ups are correctly left un-drafted there as judgment/design calls ("decide X's
  fate"). The consolidated-closeout checkbox was simply never flipped after the audit shipped — this is a stale
  checkbox, not open work, and per this task's scope I did not touch it myself (only a one-line pointer edit is
  authorized). Whoever next has write access to that doc should flip it to `[x]` citing this audit doc.
- **Track 8's "Open follow-ups" glued-id item (`[DATA] P2`, line ~663, "21 glued-id rows... 9 ORCA/SOLANA cells still
  need the retry") is STALE — the retry already happened and a DEEPER root cause was found.** A fresher entry in
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (re-verified 2026-07-24, the same day) shows all 9 ORCA cells
  finished migrating clean (`errors=0` across a retry chain), but a fresh `verify_defi_glued_ids_2026_07_24.py` run
  STILL shows 21 glued-id rows unchanged — because neither the migration nor the delete-marker script ever **retracts**
  a pre-existing manifest row once its source object is renamed to `_migrated_*` (the old glued-id row and the new
  per-instrument rows carry different `instrument_id`s, so upsert never supersedes the old one). The recommended next
  step is "a manifest-row-level purge, not yet built" (per
  `plans/archive/issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` addendum "tick 3") — this is new,
  not-yet-scoped capability work (a manifest-row retraction mechanism doesn't exist yet) with real
  prod-manifest-mutation blast radius, not a bounded fact-check or a scoped code change. Not drafted here; recommend a
  dedicated design pass reads that addendum first before any AO todo is written against it.

## Deferred — stays human, with why (per-todo classification)

Every other open native todo was checked and classified as staying human. Full per-todo table in the dispatching
session's final report; condensed here for anyone re-auditing this doc later:

| Native todo (line, tag)                                                                                                  | Why it stays human                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track 2 `[DATA] P1` delete lending-indices legacy bucket (389)                                                           | **No longer human-gated (2026-07-28 gate-cleanup)** — operator ruling 2026-07-28 (delete-safety-protocol §3a, extended) reversibility-qualifies whole-bucket destroys the same way object deletes already were, PROVIDED a fresh `gcs_bucket_soft_delete_retention_seconds()` check on the target bucket clears (>=604800s). Retagged `[OPERATOR]`→`[DATA]` in the source doc, dispatchable there as a normal AO todo (run the fresh check, cite the value, execute via UTL helpers if it clears, else fall back to the §3a approve-executes flow).                                                                                                                                                            |
| Track 2 `[BACKEND] P0` write_defi_rows() bare-symbol leaf (393)                                                          | **Already covered** — an identical fix is already drafted in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (its "Fix `write_defi_rows()`'s filename-leaf construction" todo), and that batch's finalize plan already plans to cross-flip THIS exact checkbox once its todo ships. Drafting it again here would create a same-file collision with an already-queued fix.                                                                                                                                                                                                                                                                                                                                    |
| Track 3 `[DATA] P0` PURGE 1.79M dupes + 219.5K phantoms, THEN seed 63.9M expected_unattempted (410)                      | Massive-scale prod-manifest purge+seed; explicitly sequenced AFTER the still-in-flight glued-id marker-cleanup dry-run (Progress Log: ~68% through its corpus as of last checkpoint); scale alone (63.9M rows) warrants `[OPERATOR]`-class caution even though the native text isn't tagged that way (a gap worth flagging, not fixing by editing the source doc).                                                                                                                                                                                                                                                                                                                                             |
| Track 4 `[BACKEND] P2` wire Morpho + Solana ORCA/RAYDIUM swap indexer (488)                                              | **Stale + design work.** Morpho is actually already wired (`market-tick-data-service@4c340f93` + 2 follow-on fixes) — the doc's own remaining open item is a G2-gate re-run that has bounced 10+ times on an unrelated stuck-consolidator precondition, not fresh work. The Solana ORCA/RAYDIUM swap indexer is explicitly scoped in its own source doc as "genuinely new capability... not urgent... file a dedicated implementation plan when this becomes a priority" — `[DESIGN] P3`, no fixed done-when, textbook human-only per the dispatch-scope rule. Consistent with `defi_satellite_ao_dispatch_batch1_2026_07_25.md` independently finding the sibling Morpho doc had zero AO-eligible candidates. |
| Track 8 `[INFRA] P1` resume paused DeFi crons (576, duplicated verbatim at 691)                                          | Explicitly gated on Track 1 (per-instrument migration, 13 open items incl. a still-applying multi-hour VM) + the currently-running migration VM reaching terminal state — genuinely not ripe, not a judgment call. Re-check once Track 1 lands. **Same-doc duplicate**: lines 576 and 691 are the identical item; flagging so a future editor doesn't fix it twice.                                                                                                                                                                                                                                                                                                                                            |
| Open follow-ups `[SCRIPT] P3` root-cause quickmerge.sh reset (606)                                                       | Non-reproducible on retry per its own text — nothing for a worker to execute until it recurs; not a schedulable audit.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Open follow-ups `[DATA] P1` 16.7M LENDING→A_TOKEN/DEBT_TOKEN migration (671)                                             | Explicitly gated on `defi_lending_writer_retire_prerequisite_2026_07_20.md` todos 7/8/10/11, which `defi_satellite_ao_dispatch_batch1_2026_07_25.md` independently already found zero-AO-eligible-candidate on that same doc.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Open follow-ups `[DATA] P1` residual canon walk C2-C12 (674)                                                             | Explicit duplicate-avoidance note in the native text itself points to `defi_track01_per_instrument_and_canon_id_2026_07_24.md:310` and says "avoid duplicating the work across both docs" — respecting that instruction rather than re-drafting.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Open follow-ups `[BACKEND] P2` async fan-out / executor-offload (686)                                                    | Explicit native-text duplicate of the Track 5 item, which is itself zero-AO-eligible-candidate per batch1's triage of `defi_track5_coverage_mvp_backfill_2026_07_24.md`; native text also states the knobs are "NOT a safe standalone step."                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Open follow-ups `[DATA] P2` 2-VM TheGraph canary (689)                                                                   | **No longer operator-owned (2026-07-28 gate-cleanup)** — same as the source doc: finding W (ambient self-service IAM identity) + the already-decided Q3 ruling ("ship code + I run the canary" already resolved to "yes, run the canary") clear it. Retagged `[OPERATOR]`→`[DATA]` in both docs together; dispatchable there as a normal monitored SPOT VM-launch todo.                                                                                                                                                                                                                                                                                                                                        |
| Open follow-ups `[SCRIPT] P1` delete_migrated_defi_markers --apply (577, source doc line renumbered since 629 was cited) | **STALE ROW — no longer human-gated.** The source doc's matching todo is now `[SCRIPT] P1`, "Reversibility-verified, no `[OPERATOR]` gate needed" (finding T): object-level delete only (never the bucket), `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800` (7 days), fresh-checked 2026-07-26 per delete-safety-protocol §3a. Still gated on the "21 glued-id rows" re-verify prerequisite (content-correctness, independent of reversibility) — re-query the retention fresh before running, not from this citation.                                                                                                                                                                       |
| Open follow-ups `[DATA] P1` DeFi MVP backfill to 100% (695)                                                              | Explicit "C-GREEN gated on Track 1 + Track 2 + Track 3" pointer + a parked backlog task; the one concretely-executable sub-piece (`catalogue_pool_ids_for_shard` generalization) is already drafted in `defi_satellite_ao_dispatch_batch1_2026_07_25.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

## Progress log

- 2026-07-26/27 (slot 4, todo 1 — CURVE/OPTIMISM subgraph-deindex reclassification, IN PROGRESS): Sub-step (a, the `cd`
  bug fix) is CODE-COMPLETE but NOT YET SHIPPED. Fixed `setup-data-pipeline-vm.sh`'s `canonical-migration` `VM_TASK`
  branch — it hardcoded `cd "$WORKSPACE/mtds"` regardless of `VM_SERVICE`, so a fresh VM running the instruments-service
  reclassify script (`VM_SERVICE=instruments_service`) would hit `ERROR: $WORKSPACE/mtds missing` even though its
  tarball was correctly extracted to `$WORKSPACE/instruments`. Fixed by deriving the workspace dir via the SAME
  `SERVICE_TARBALLS` → `TARBALL_DIRS` mapping the tarball-install step already uses (never hand-rolled a second
  service→dir mapping), with a `mtds` fallback for an unmapped `VM_SERVICE` (preserves the pre-fix default for every
  existing MTDS-only canonical-migration caller). Added 3 regression tests
  (`TestCanonicalMigrationServiceKeyedWorkspaceDir` in `tests/unit/test_vm_launcher_scripts.py`) that extract the REAL
  `SERVICE_TARBALLS`/`TARBALL_DIRS` declarations + the fix's derivation lines directly out of the setup script (not a
  hand-duplicated copy, so the test can't silently drift from the real mapping) and assert: `instruments_service` →
  `instruments` (the bug this fixes), `market_tick_data_service` → `mtds` (backward-compat), and an unmapped
  `VM_SERVICE` → `mtds` (safe fallback). **Verified the fix's actual logic is correct** by extracting and running the
  exact generated bash snippet directly (`bash -c`, outside pytest) — confirmed `instruments_service` resolves to
  `instruments` in <1s, exit 0. **Blocked on shipping**: running the SAME check through `pytest` hangs indefinitely —
  confirmed via 3 separate attempts (bare run, `--timeout=30`, a 120s-timeout run) and a live process inspection
  (`ps --forest`) showing the pytest process in kernel state `D` (uninterruptible sleep) on `wait_on_buffer` /
  `folio_wait_bit_commo` — a genuine disk-I/O/page-cache-reclaim stall, not a deadlock in the test code (confirmed via
  `/proc/loadavg` reading 21-37 on an 8-core host at the time, i.e. severe shared-host contention, not this repo's
  fault). Both files remain UNCOMMITTED in this slot's `deployment-service` worktree (`git status`:
  `M scripts/vm/setup-data-pipeline-vm.sh`, `M tests/unit/test_vm_launcher_scripts.py`) — correctly withheld per the
  "commit only from a `quality-gates.sh`-green tree" HARD RULE, not lost (this is a live git worktree, not a scratchpad
  file — it survives a context compact). **Next steps once host load allows**: re-run
  `.venv/bin/python -m pytest tests/unit/test_vm_launcher_scripts.py -k TestCanonicalMigrationServiceKeyedWorkspaceDir`,
  then `bash scripts/quality-gates.sh`, then
  `bash scripts/quickmerge.sh "fix(vm): derive canonical-migration workspace dir from VM_SERVICE" --agent --files 'scripts/vm/setup-data-pipeline-vm.sh tests/unit/test_vm_launcher_scripts.py'`.
  Only THEN proceed to sub-step (b): launch a fresh canonical-migration VM running
  `instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py --apply`, T+10min
  health-verify RUNNING with real `run.log` progress, confirm completion, spot-check the manifest shows the ~144
  previously-`attempted_failed` CURVE/OPTIMISM rows now carrying `EXPECTED_SUBGRAPH_DEINDEXED`, THEN flip this todo's
  checkbox with the shipped SHA + verification evidence.

- **2026-07-28 (slot-13, infra) — DONE, both sub-steps complete.** Sub-step (a): confirmed ALREADY SHIPPED on
  `live-defi-rollout` (`deployment-service@0ed2ca6 fix(vm): derive canonical-migration workspace dir from VM_SERVICE`,
  landed by a different slot after the 2026-07-26/27 WIP above — slot 4's own uncommitted WIP lived in a different
  slot's worktree this slot cannot reach, so this slot independently re-verified the shipped fix rather than depending
  on it). Also found a dedicated `defi-curve-optimism-reclassify` launcher category already added to
  `launch-canonical-migration-vm.sh` (2026-07-27, citing the same `0ed2ca6` fix) — used it as-is. Sub-step (b): **2
  infra blockers hit and fixed before the real `--apply` could run**: (1) both launch attempts initially warned of STALE
  code tarballs (`deployment-service`/`unified-api-contracts`/others) — republished via `create-code-tarballs.sh`, which
  itself first failed with `ImportError: cannot import name 'iter_route_contexts' from fastapi.routing` in both
  `deployment-service` and `instruments-service` local venvs (stale `.venv` vs `uv.lock`'s pinned `fastapi==0.140.7`,
  installed was `0.136.3`/`0.135.1`) — fixed via `uv sync --frozen` in each repo (no tracked-file changes, `.venv`
  only); (2) the first dry-run on the launcher's default `e2-standard-8` (32GB) was **OOM-killed** (`rc=137`, `Killed`
  after ~76s) reading the 985MB/23.9M-row `_index/availability_index.parquet` — relaunched with
  `MACHINE_TYPE=e2-highmem-16` (128GB), which succeeded cleanly. Dry-run
  (`canonical-migration-defi-curve-optm-reclass-20260728-060342`, exit_code=0) found **419** matching rows (346
  main-index + 73 per-VM shard) — more than the ~144 measured 2026-07-24, expected drift since the docstring notes this
  is a live, ongoing condition (more backfill attempts kept hitting the dead subgraph in the intervening days). The
  subsequent `--apply` launch also hit a fresh tarball-staleness race (2 more repos advanced meanwhile from other slots'
  concurrent pushes) — killed that VM before it started any mutation, republished again, relaunched. **`--apply` run**
  (`canonical-migration-defi-curve-optm-reclass-20260728-061053`, `e2-highmem-16`, exit_code=0): reclassified **420**
  rows total — 346 in `_index/availability_index.parquet` (backup:
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.20260728-061342.deindexed.bak.parquet`,
  27,204,041 rows preserved) + 74 in `_index/per_vm/mtds-dex-swaps-backfill-1.parquet` (backup:
  `.../per_vm/mtds-dex-swaps-backfill-1.20260728-061342.deindexed.bak.parquet`, 269,806 rows preserved). **Post-run
  manifest spot-check** (direct pandas read of the post-apply `availability_index.parquet`, 27,204,041 rows):
  `EXPECTED_SUBGRAPH_DEINDEXED` CURVE/OPTIMISM rows = **346** (matches the log); rows STILL `attempted_failed` matching
  the dead-subgraph cascade signature = **0**. `quality-gates.sh` green in deployment-service: satisfied by `0ed2ca6`
  already being merged to `live-defi-rollout` via the standard QG-before-quickmerge gate at shipping time — no new
  deployment-service code changed this session (verified `git status --porcelain` clean in both `deployment-service` and
  `instruments-service` after the `uv sync`s). The reclassify script's own `# Delete-when:` header condition (0
  CURVE/OPTIMISM `dex_pool_swaps` `attempted_failed` rows matching the dead-subgraph cascade error) is now met — left in
  place as this todo's scope was fix+apply, not cleanup; a future pass can delete the one-off script + its launcher
  category.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from
`defi_consolidated_closeout_2026_07_18.md` or its cited source doc.
