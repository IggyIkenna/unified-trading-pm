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
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
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
---

# DeFi consolidated closeout — native-todo AO extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review. All 4 todos
> below touch distinct files/repos and are same-priority-within-doc, so they are safe to dispatch concurrently once
> activated.

## Todos

- [ ] [INFRA] P2. **Combined fix + apply for the CURVE/OPTIMISM subgraph-deindex reclassification (2 sub-steps, causally
      sequential — the 2nd is blocked on the 1st):** (a) fix `setup-data-pipeline-vm.sh`'s `canonical-migration` branch
      (`:1187`) which hardcodes `cd "$WORKSPACE/mtds"` regardless of `VM_SERVICE` — mirror the `VM_SERVICE`-keyed
      `cd "$WORKSPACE/instruments"` pattern already used by other branches (e.g. `:1224`) so an instruments-service
      script can be found and run from this VM path; (b) once (a) lands, launch a fresh canonical-migration VM running
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
- [ ] [DATA] P2. **Real column-prune refactor of `measure_honest_coverage.py`** so the nightly honest-coverage VM no
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
      `defi_consolidated_closeout_2026_07_18.md` Track 8 as part of "fix the honest-coverage-nightly right-size").
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
- [ ] [DOC] P1. **Add the missing digest entry for `defi_track01_per_instrument_and_canon_id_2026_07_24.md` into
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
      `[DOC] P1` todo).

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

| Native todo (line, tag)                                                                             | Why it stays human                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track 2 `[OPERATOR] P1` delete lending-indices legacy bucket (389)                                  | Already `[OPERATOR]`-tagged, prod GCS delete, human-gated by its own text.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Track 2 `[BACKEND] P0` write_defi_rows() bare-symbol leaf (393)                                     | **Already covered** — an identical fix is already drafted in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (its "Fix `write_defi_rows()`'s filename-leaf construction" todo), and that batch's finalize plan already plans to cross-flip THIS exact checkbox once its todo ships. Drafting it again here would create a same-file collision with an already-queued fix.                                                                                                                                                                                                                                                                                                                                    |
| Track 3 `[DATA] P0` PURGE 1.79M dupes + 219.5K phantoms, THEN seed 63.9M expected_unattempted (410) | Massive-scale prod-manifest purge+seed; explicitly sequenced AFTER the still-in-flight glued-id marker-cleanup dry-run (Progress Log: ~68% through its corpus as of last checkpoint); scale alone (63.9M rows) warrants `[OPERATOR]`-class caution even though the native text isn't tagged that way (a gap worth flagging, not fixing by editing the source doc).                                                                                                                                                                                                                                                                                                                                             |
| Track 4 `[BACKEND] P2` wire Morpho + Solana ORCA/RAYDIUM swap indexer (488)                         | **Stale + design work.** Morpho is actually already wired (`market-tick-data-service@4c340f93` + 2 follow-on fixes) — the doc's own remaining open item is a G2-gate re-run that has bounced 10+ times on an unrelated stuck-consolidator precondition, not fresh work. The Solana ORCA/RAYDIUM swap indexer is explicitly scoped in its own source doc as "genuinely new capability... not urgent... file a dedicated implementation plan when this becomes a priority" — `[DESIGN] P3`, no fixed done-when, textbook human-only per the dispatch-scope rule. Consistent with `defi_satellite_ao_dispatch_batch1_2026_07_25.md` independently finding the sibling Morpho doc had zero AO-eligible candidates. |
| Track 8 `[INFRA] P1` resume paused DeFi crons (576, duplicated verbatim at 691)                     | Explicitly gated on Track 1 (per-instrument migration, 13 open items incl. a still-applying multi-hour VM) + the currently-running migration VM reaching terminal state — genuinely not ripe, not a judgment call. Re-check once Track 1 lands. **Same-doc duplicate**: lines 576 and 691 are the identical item; flagging so a future editor doesn't fix it twice.                                                                                                                                                                                                                                                                                                                                            |
| Open follow-ups `[SCRIPT] P3` root-cause quickmerge.sh reset (606)                                  | Non-reproducible on retry per its own text — nothing for a worker to execute until it recurs; not a schedulable audit.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Open follow-ups `[DATA] P1` 16.7M LENDING→A_TOKEN/DEBT_TOKEN migration (671)                        | Explicitly gated on `defi_lending_writer_retire_prerequisite_2026_07_20.md` todos 7/8/10/11, which `defi_satellite_ao_dispatch_batch1_2026_07_25.md` independently already found zero-AO-eligible-candidate on that same doc.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Open follow-ups `[DATA] P1` residual canon walk C2-C12 (674)                                        | Explicit duplicate-avoidance note in the native text itself points to `defi_track01_per_instrument_and_canon_id_2026_07_24.md:310` and says "avoid duplicating the work across both docs" — respecting that instruction rather than re-drafting.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Open follow-ups `[BACKEND] P2` async fan-out / executor-offload (686)                               | Explicit native-text duplicate of the Track 5 item, which is itself zero-AO-eligible-candidate per batch1's triage of `defi_track5_coverage_mvp_backfill_2026_07_24.md`; native text also states the knobs are "NOT a safe standalone step."                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Open follow-ups `[OPERATOR] P2` 2-VM TheGraph canary (689)                                          | Already `[OPERATOR]`-tagged; operator explicitly owns launching the canary per a prior ruling.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Open follow-ups `[OPERATOR] P1` delete_migrated_defi_markers --apply (629)                          | Already `[OPERATOR]`-tagged, prod-bucket-adjacent delete, human-gated by its own text; also still blocked on the in-flight dry-run finishing.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Open follow-ups `[DATA] P1` DeFi MVP backfill to 100% (695)                                         | Explicit "C-GREEN gated on Track 1 + Track 2 + Track 3" pointer + a parked backlog task; the one concretely-executable sub-piece (`catalogue_pool_ids_for_shard` generalization) is already drafted in `defi_satellite_ao_dispatch_batch1_2026_07_25.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from
`defi_consolidated_closeout_2026_07_18.md` or its cited source doc.
