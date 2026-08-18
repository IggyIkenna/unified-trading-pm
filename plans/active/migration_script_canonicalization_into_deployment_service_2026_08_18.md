---
doc_type: plan
title: Canonicalize fleet migration/one-off scripts into deployment-service — mirror the VM-launcher SSOT
summary: >-
  Operator direction (2026-08-18) — every service's ad-hoc migration/backfill/one-off script should route through
  ONE canonical structure in deployment-service, the same discipline already codified for VM launchers
  (`/codex/05-infrastructure/launcher-script-ssot.md`), "so it's not like a new thing" and we "never deploy [a
  migration] from the repo itself directly." Real fleet discovery (this doc's own §Discovery, not a placeholder)
  found ~619 migration-shaped scripts across 9 repos outside deployment-service, ~99% already carrying a
  `Lifecycle: oneoff` marker with a satisfied-or-satisfiable `Delete-when` condition — meaning most of that count is
  working-as-intended TEMPORARY scaffolding under the existing script-homes.md discipline, not a per-file relocation
  target. **Revised 2026-08-18 (operator pushback, same day)**: that population IS still the plan's real deliverable
  material, just not via relocation — real structural-signature evidence across all 619 files (83% already hand-roll
  argparse, 70% dry-run, 75% `get_storage_client()`, 65% `--confirm`/`--apply`) shows the SAME handful of operation
  shapes (purge/delete, canonicalize/relabel, migrate schema, backfill/populate, reconcile/repair, read-only
  audit) being reinvented from scratch fleet-wide — exactly the "hacky, ad-hoc, no shared canonical pattern" problem
  the operator is naming, not a reason to leave the audit closed. §Pattern clustering below turns that audit into 5
  canonical, parameterizable templates (Phase 0b) — the actual deliverable, distinct from and more valuable than
  file relocation. The REAL actionable population is now fourfold — (1) the 16 Category-1 GCS-bug files already
  fully triaged in `utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`, (2) ~55 `permanent`/
  `campaign`/`reusable-*`-marked scripts across instruments-service + market-tick-data-service that are genuinely
  recurring, not one-shot, (3) the 5 canonical templates built FROM the ~619-file audit (Phase 0b, new), and (4) the
  POLICY change itself — new codex SSOT + a script-homes.md correction making the canonical-template path the
  sanctioned DEFAULT for any new recurring-shaped need, with the Lifecycle/Delete-when convention remaining valid
  only for genuinely one-of-a-kind, never-to-recur scripts.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    deployment-service,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    unified-trading-library,
    client-reporting-api,
    deployment-api,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [scripts, script-homes, migration, deployment-service, canonicalization, gcs, one-off-scripts, launcher-ssot]
related:
  [
    /codex/05-infrastructure/launcher-script-ssot.md,
    /codex/06-coding-standards/script-homes.md,
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 10.5
estimate_calibrated_ai_days: 8.4
assigned_role: infra
effort: high # 11-repo fleet-wide discovery + canonicalization + 5 canonical templates, multi-phase — not a small fix
drift_direction: advance-code
depends_on:
context_scope:
  [
    /codex/05-infrastructure/launcher-script-ssot.md,
    /codex/06-coding-standards/script-homes.md,
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    market-tick-data-service/scripts/migration_common.py,
    instruments-service/scripts/migrations/__init__.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Operator directive 2026-08-18 (verbatim): \"It would also make sense to just move all scripts, even migration
    scripts and per[iodic] scripts, because this is stuff that we do quite a lot, we can sort of canonise it in the
    deployment service ... It just forces a structure that we never deploy from the repo itself directly. This would
    require going through every single service and making sure that it's all moved.\"",
    "Operator pushback 2026-08-18 (verbatim, same day, relayed via coordinator): \"But we also will need to ensure
    that we build on top of the canonical rather than build on top of the hacky Claude hard rules. I do consider
    migrations and deletions not completely temporary. Even if they were done once, we might well reuse those same
    patterns to build another script, making canonical versions where we can easily adjust those rather than always
    have to build a new one, which would be good.\"",
  ]
locked_by:
locked_since:
---

# Canonicalize fleet migration/one-off scripts into deployment-service

## Why (operator's own framing — do not narrow this without flagging it)

Every service repo grows its own ad-hoc migration/backfill/one-off scripts that talk to GCS directly, each
reinventing the wheel — sometimes badly: the sibling issue doc
(`/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`) found 16 files (22
call sites) in instruments-service + strategy-service calling GCS methods that don't exist on UTL's
`GCSBlobHandle`, silently swallowed by a defensive guard — direct evidence of scripts NOT going through any shared,
reviewed pattern. deployment-service already solved this problem once, for VM launchers
(`/codex/05-infrastructure/launcher-script-ssot.md`, live since 2026-05-07: "every script that runs `gcloud compute
instances create` MUST live under `deployment-service/scripts/vm/`"). The operator wants the SAME discipline applied
to migration/one-off scripts: every service routes through ONE canonical structure in deployment-service instead of
growing its own, "so it's not like a new thing" — deployment-service's own migration scripts already use the correct
`get_storage_client()` → `upload_bytes`/`download_as_bytes` pattern (verified below), unlike 16 of instruments-
service's own.

**2026-08-18 pushback (same day)**: the operator's follow-up correction (verbatim in `source:` above) sharpens this
further — it is not enough to relocate files. A script instance that ran once and self-deleted still implemented a
reusable SHAPE, and today's sanctioned default (write a fresh repo-local one-off, tag it `Lifecycle: oneoff`, let it
self-delete) is itself the anti-pattern going forward, because it means that shape gets reinvented from scratch
every time instead of adapted from a canonical, parameterizable version. §Pattern clustering and Phase 0b below are
the direct response to that correction.

## Pre-task conflict check (done 2026-08-18)

Grepped `plans/active/` + `plans/active/issues/` for `migration.script|script.canoniz|canonicaliz.*script|one.off
.script|migration.*consolidat` and for `deployment_engine`/`scripts/migrations` — no existing plan covers this exact
scope. Nearest neighbors, both genuinely siblings (cross-linked in `related:` above, not duplicated):

- `/codex/05-infrastructure/launcher-script-ssot.md` — the precedent this plan mirrors, VM launchers only (scope
  table explicitly excludes "local script that runs in-process" and non-VM-launching orchestration — migration
  scripts are exactly that carve-out, so this plan is the deliberate NEXT step, not a duplicate).
- `/plans/active/repo_scripts_governance_audit_2026_06_18.md` — governs `scripts/` lint/typecheck policy + the
  `Lifecycle`/`Delete-when` marker convention **fleet-wide** (this plan leans heavily on that marker to classify the
  discovery inventory below, see §Discovery) but does NOT address WHERE a script lives, only its lint/marker
  compliance. Cross-linked, not overlapping.
- `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` — the CONCRETE seed
  list for this plan's Phase 1 (the 16 Category-1 files); that issue doc explicitly says its own Follow-up item 1
  "needs an AO-vs-human dispatch-scope decision from the operator before authoring" — this plan IS that decision
  (human/local, per the operator's explicit instruction for this authoring task).

## Scope decision — flagged for operator confirmation, not silently assumed

**The literal instruction is "move all scripts."** Real discovery below found ~619 migration-shaped scripts fleet-
wide, and ~99% of them already carry `Lifecycle: oneoff` + a stated `Delete-when` condition under the EXISTING
script-homes.md discipline — meaning most are already-scoped, self-deleting artifacts (many likely already run in
prod and awaiting a `Delete-when` garbage-collection pass, not active tooling). Force-relocating ~550 already-
scheduled-for-deletion files would be pure churn with no behavior change, and arguably fights the TEMPORARY-by-design
intent script-homes.md already established for them (2026-06-10, reinforced 2026-06-18). **This plan's default
scope is therefore**:

1. Fix + (where still-needed) relocate the 16 already-triaged Category-1 GCS-bug files (Phase 1 — concrete, ready).
2. Relocate the ~55 `permanent`/`campaign`/`reusable-*`-marked scripts in instruments-service + market-tick-data-
   service — these are the genuinely recurring ones, "stuff we do quite a lot" in the operator's own words (Phase 3).
3. Relocate every migration-shaped script in the smaller repos regardless of Lifecycle value, since their volume is
   small enough that full relocation is cheap and the operator's instruction was unqualified (Phase 2).
4. Change the POLICY going forward (Phase 0 + Phase 4) so every NEW migration script — the ongoing "stuff we do
   quite a lot" — is authored directly in the canonical home, adapting a Phase 0b template rather than starting
   from scratch.
5. **Individual existing files in the ~500 already-`oneoff`-marked instruments-service/MTDS population mostly do NOT
   need physical relocation** — that narrow-scope judgment stands (operator confirmed "keep narrow scope" when
   asked) and the existing `Delete-when`-driven pruning discipline
   (`/codex/06-coding-standards/script-homes.md` § "Pruning is `Delete-when`-driven") still governs each file's own
   lifecycle. **This is NOT "out of scope, ignore it," and the ~619-file audit is not closed** — per the operator's
   2026-08-18 pushback (verbatim in this doc's `source:`): even a self-deleting one-shot script instance implements
   a SHAPE (purge stale rows, backfill a missing column, canonicalize a schema field, …) that recurs across the
   fleet regardless of any one file's own lifespan, and today's sanctioned default — write a fresh repo-local
   one-off, tag it `Lifecycle: oneoff`, let it self-delete — means that shape gets reinvented from scratch every
   time instead of adapted from something canonical. The audit already done (§Discovery, §Pattern clustering) is
   exactly the raw material for designing the canonical templates Phase 0b builds — treat it as template-design
   input, not a closed, disposable inventory. If the operator separately wants the literal FULL FILE-RELOCATION
   sweep too, that remains a separate, much larger follow-up plan (bulk-rename ~500 files across 2 repos) this doc
   does not authorize on its own; flag at plan review, don't silently execute a 500-file move under a P2 human plan.

---

## Discovery — real fleet inventory (2026-08-18, `find`/`grep` against the live tree, not a placeholder)

### Method

`find <repo>/scripts -type f \( -name "*.py" -o -name "*.sh" \)` filtered to names matching
`migrat|backfill|repair|fix_|cleanup|clean_up|one_off|oneoff|_20YY_MM_DD|reconcile|purge|wipe_|dedupe|dedup_`,
excluding `__pycache__`, across every repo in this workspace. Cross-checked against each hit's own
`# Lifecycle:`/`# Delete-when:` marker (per `repo_scripts_governance_audit_2026_06_18.md`'s convention) where
present.

### Per-repo counts (migration-shaped scripts in that repo's OWN `scripts/`, outside deployment-service)

| Repo | Matching scripts | Date-stamped (`_20YY_MM_DD`) | Has `# Lifecycle:` marker |
|---|---|---|---|
| instruments-service | 290 | 241 (83%) | 285/290 (98%) |
| market-tick-data-service | 276 | 253 (92%) | 270/275 (98%) |
| unified-trading-pm | 59 | — | not sampled — **excluded, see below** |
| e2e-testing | 23 | — | not sampled — **partially excluded, see below** |
| features-service | 18 | 11 | not sampled |
| market-data-processing-service | 13 | 9 | not sampled |
| agent-orchestrator | 12 | 1 | not sampled — **excluded, see below** |
| strategy-service | 2 | 0 | not sampled |
| unified-trading-library | 2 | 1 | not sampled |
| client-reporting-api | 1 | 0 | not sampled |
| deployment-api | 1 | 0 | not sampled |
| **Fleet total in-scope repos** (excl. PM + AO, incl. all others) | **~628** | — | — |

Zero hits (confirmed, not assumed): deployment-ui, unified-trading-system-ui, unified-api-contracts,
system-integration-tests, ibkr-gateway-infra, greeks-service, fund-administration-service, trading-agent-service,
batch-live-reconciliation-service, ml-service, alerting-service, unified-trading-api.

### Lifecycle-marker breakdown for the two mega-repos (mechanical, not judgment)

Because adoption of the `# Lifecycle:` marker is ~98% in both instruments-service and market-tick-data-service, the
one-shot-vs-recurring split is **mostly mechanical**, not a fresh per-file read:

- **instruments-service**: 225+16 variants = ~241 `oneoff`/`one-off` (already dated-or-DELETE-conditioned), 7
  `campaign`, 6 `permanent`, 1 `temporary`.
- **market-tick-data-service**: 154+8+~40 variants = ~230 `oneoff`/`one-off`, 17 `campaign`, 6 `permanent`, 4
  `reusable-investigation`, several `reusable-narrow`/re-runnable-check.

The `permanent`/`campaign`/`reusable-*` files are the plan's real relocation targets (Phase 3); the `oneoff` bulk is
NOT a relocation target (§Scope decision item 5) but IS the primary raw material for §Pattern clustering /
Phase 0b's template design below — that distinction is the point of this revision.

### Repo-by-repo exclusions (with rationale — not silently dropped)

- **agent-orchestrator (12 scripts)** — confirmed via read of `scripts/orchestrator/apply_content_id_migration.py`:
  these migrate AO's OWN internal `state.db`/`backlog.yaml`, a fundamentally different data store from the GCS
  trading-data buckets deployment-service governs. Moving AO's internal-state tooling into a different repo would
  break locality for no benefit — AO is a single, self-contained service (per
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`). **Excluded from this plan's scope.**
- **unified-trading-pm (59 scripts)** — sampled the list (`scripts/cicd/migrate_repo_to_git_tag.py`,
  `scripts/migration/copy-clean-repos.sh`, `scripts/dev/migrate-slots-to-pathb.sh`, etc.): these are PM-repo-internal
  workspace/session/CI tooling (git-tag migration, slot layout migration, stale-tmp cleanup), not trading-data GCS
  migrations. **Excluded from this plan's scope** — the one flagged Category-2 file
  (`scripts/catalogue/sync-to-mock.py`, raw `google.cloud.storage` import, per the sibling issue doc) is a
  coding-standard note, not a relocation candidate (deployment-service is a trading-data/deploy surface; PM's own
  catalogue-sync tooling belongs with PM).
- **e2e-testing (23 scripts, partial)** — this list is a MIX: several are VM launchers (`launch_*_vm.sh`,
  `setup-backfill-vm.sh`) already governed by `/codex/05-infrastructure/launcher-script-ssot.md`'s own deferred-
  launcher table — **out of THIS plan's scope, that SSOT's job**. The genuine GCS-migration-shaped subset — 6 files
  — **IS in scope** (Phase 2): `scripts/defi/migrate_legacy_twins_from_audit.py`,
  `scripts/defi/migrate_uniswap_v4_legacy_to_canonical.py`,
  `scripts/defi/copy_lst_yields_prd_to_canonical_2026_07_14.py`,
  `scripts/sports/migrate_sports_md_unmappable_to_canonical_2026_06_19.py`,
  `scripts/sports/delete_sports_legacy_twinned_2026_06_19.py`,
  `scripts/sports/verify_sports_md_unmappable_twins_2026_06_19.py`.

---

## Pattern clustering — recurring shapes across the ~619-script population (added 2026-08-18, operator-pushback revision)

Per the operator's 2026-08-18 pushback (verbatim in `source:`): the "leave the ~500 oneoff scripts alone" framing
above must not read as "out of scope, ignore." Even a script that runs once and self-deletes implements a reusable
SHAPE, and today's sanctioned default (write a fresh repo-local one-off, tag it, let it self-delete) means that
shape gets reinvented from scratch every time. This section re-derives the population LIVE (not reused blindly from
the authoring session's counts — see the bug caught below) and clusters it by operation-shape, not by individual
file, to identify what a canonical template roster should look like.

### Re-derivation method (this revision, 2026-08-18)

Same `find`+regex method as §Discovery, re-run fresh rather than trusting the authoring session's counts at face
value. Caught and fixed a real bug on the first re-derivation attempt: piping `find "$repo/scripts" ...` output
through `sed "s|^|$repo/|"` double-prefixed paths `find` already returned repo-prefixed
(`instruments-service/instruments-service/scripts/...`), which silently zeroed out every downstream `grep -l`
structural check (0 files "had" argparse — an implausible result, not accepted at face value, which is what
surfaced the bug). Corrected population: **619 files** (vs. the authoring session's ~628 — the ~1.5% difference is
expected re-derivation noise from slightly different exclusion handling, not a discrepancy worth chasing further).

### Structural-signature evidence (real grep counts across all 619 files, not a sample)

| Signature | Files | % |
|---|---|---|
| `# Lifecycle:` marker present | 614 | 99% |
| `argparse`/`add_argument`/`ArgumentParser` | 511 | 83% |
| `--confirm`/`--apply` flag | 400 | 65% |
| `dry_run`/`dry-run` | 432 | 70% |
| `get_storage_client()` (correct UTL pattern) | 462 | 75% |
| `ManifestWriter`/`ManifestReader`/`manifest_index`/`read_availability_index` | 162 | 26% |

This is the concrete evidence for the operator's point: at least 3 of 4 files already hand-roll the SAME argparse +
dry-run + confirm/apply + storage-client scaffold independently — proof the shape is reinvented every time, not
proof it doesn't recur.

### Operation-shape clustering (basename keyword pass, ordered precedence, then sample-verified)

| # | Cluster | Files | % | Representative names |
|---|---|---|---|---|
| 1 | **Row-removal / purge** (purge, delete, retire, decommission, wipe, cleanup, dedupe) | 110 | 18% | `purge_bad_prediction_manifest_rows.py`, `wipe_pre_floor_sports_2026_07_21.py`, `dedupe_manifest_schema_drift.py` |
| 2 | **Field/path canonicalization & schema migration** (canonicalize, relabel, migrate, manifest-relocate/consolidate) | 170 | 27% | `canonicalize_defi_manifest_venue_2026_06_14.py`, `migrate_dex_pool_columns.py`, `reclassify_kalshi_other_historical.py` |
| 3 | **Drift reconciliation & repair** (reconcile, repair, fix, remediate, correct) | 66 | 11% | `reconcile_phantom_manifest_rows.py`, `mtds_reconcile_partition_mismatch.py`, `fix_prediction_manifest_and_gcs_2026_05_22.py` |
| 4 | **Backfill / populate missing value** (backfill, restamp, stamp, populate, refresh, expand) | 108 | 17% | `backfill_cefi_source_column.py`, `restamp_sports_candle_venue_2026_08_03.py` |
| 5 | **Read-only audit / investigation / verification** (census, measure, survey, audit, characterize, trace, sweep, verify, validate, close/scope-coverage-gap) | 74 | 12% | `teams_coverage_census_2026_08_05.py`, `verify_legacy_bucket_decommission_precondition.py`, `measure_cefi_catalogue_enumeration_gap_2026_07_23.py` |
| — | Uncategorized by this keyword pass | 91 | 15% | see below |

**528/619 (85%) cluster cleanly into 5 shapes on a first keyword pass alone.** The remaining 91 (15%) were sample-
inspected (20-file random sample, not assumed one-of-a-kind from the miss alone): most turned out to be SYNONYM
variants of the same 5 shapes that the keyword regex simply didn't catch — `reclass_*` (short for reclassify →
cluster 2), `flip`/`reflip` (state-correction → cluster 3), `restore` (→ cluster 3), `quarantine` (→ cluster 1),
`investigate`/`report`/`profile`/`walk`/`smoke` (→ cluster 5), and files already living under a literal `backfill/`
subdirectory whose basename doesn't itself contain "backfill" (→ cluster 4). A genuine handful are one-of-a-kind
(e.g. `profile_2018_06_17_memory.py`, a one-time memory-profiling script). **Net read: the true one-of-a-kind
population is smaller than 91/619, and this 5-cluster structure is a conservative floor, not an overfit** —
consistent with "a reasonable pass," not a claim of perfect clustering.

---

## Phase 0 — settle the canonical shape in deployment-service FIRST

deployment-service's OWN migration-shaped scripts are functionally correct but structurally inconsistent — this
phase must land before other repos' scripts have anywhere sound to move to.

**Current state (verified 2026-08-18)**: `deployment-service/scripts/` root already holds 6 migration/one-off-
shaped scripts flat alongside ~35 setup/deploy/sync/provision scripts — `migrate_sports_league_sharding.py`,
`validate_league_migration.py`, `rebuild_sports_manifest.py`, `wipe_pre_floor_sports_2026_07_21.py`,
`wipe_sports_reference_v2_post_floor_2026_08_04.py`, `bootstrap_operational_data_bq.py`. Confirmed via
`grep -n "upload_from_string\|upload_bytes\|get_storage_client"` on each: **all already use the CORRECT
`get_storage_client()` → `storage_client.upload_bytes(...)` pattern** (`migrate_sports_league_sharding.py:187`,
`rebuild_sports_manifest.py:260`) — no bug-fix needed here, only relocation + a shared library extraction. There is
**no dedicated `scripts/migrations/` subdirectory** the way `scripts/vm/` exists for launchers — that is the gap
this phase closes.

- [x] [INFRA] P1. Create `deployment-service/scripts/migrations/` with one subdirectory per SOURCE repo
      (`deployment-service/scripts/migrations/self/`, `.../instruments-service/`, `.../market-tick-data-service/`,
      `.../market-data-processing-service/`, `.../features-service/`, `.../strategy-service/`,
      `.../unified-trading-library/`, `.../client-reporting-api/`, `.../deployment-api/`, `.../e2e-testing/`) —
      repo-scoped subdirectories avoid a 600+-file flat dump and a rename collision risk, mirroring how
      `scripts/vm/` groups launchers by `{asset_group}-{flavor}` prefix rather than one flat namespace. Done-when:
      directories exist with a `README.md` stub in `scripts/migrations/` stating the convention (one paragraph,
      cites this plan + `migration-script-ssot.md` (Phase 4 — not yet created, this plan authors it) once landed) —
      the README stub also gets Phase 0b's "Template roster" table once that phase lands.
      **✅ DONE (2026-08-18)** — all 10 subdirectories created; README stub cites this plan (not
      `migration-script-ssot.md`, correctly deferred since Phase 4 hasn't landed it yet).
- [x] [INFRA] P1. Move deployment-service's own 6 flat-root migration scripts (named above) into
      `scripts/migrations/self/`, updating any caller (Makefile targets, README references, Cloud Scheduler /
      Terraform triggers if any invoke them by path — `grep -rn` the 6 filenames across `deployment-service/` +
      `deployment-service/terraform/` first). This is the PROOF-OF-CONCEPT move that establishes the pattern before
      other repos' scripts land here. Done-when: `git mv` complete, `bash deployment-service/scripts/quality-
      gates.sh` green, no dangling reference (`grep -rn "scripts/migrate_sports_league_sharding\|scripts/
      rebuild_sports_manifest\|scripts/validate_league_migration\|scripts/wipe_pre_floor_sports\|scripts/
      wipe_sports_reference_v2_post_floor\|scripts/bootstrap_operational_data_bq"` outside `scripts/migrations/self/`
      returns nothing).
      **✅ DONE (2026-08-18)** — all 6 files `git mv`'d. Pre-move `grep -rn` across the whole repo (Makefile,
      terraform/, README.md, tests/, quality_gates/, pyproject.toml) found exactly one real caller —
      `scripts/setup-pubsub.sh` (2 lines, a comment + an echo string referencing `bootstrap_operational_data_bq.py`)
      — updated to the new path. Two substring matches on `rebuild_sports_manifest` in
      `vm_prefix_registry.py`/`launch-sports-v9-migration-vm.sh` confirmed as false positives (a DIFFERENT script,
      `rebuild_sports_manifest_v9`, in a different repo). Also fixed 4 of the 6 moved scripts' own internal
      `Usage:` docstring examples showing the stale pre-move invocation path (a stale self-reference is a finding
      per this workspace's own doc-hygiene rule, fixed in the same commit rather than left to rot). `bash
      deployment-service/scripts/quality-gates.sh --no-fix` green; final dangling-reference grep empty. Shipped
      `deployment-service@b7fb15841c`.
- [ ] [INFRA] P2. Extract `deployment-service/scripts/migrations/lib/migration_common.py` — a GENERIC scaffolding
      module (mirrors `deployment-service/scripts/vm/lib/launcher_common.sh`'s DRY role for launchers), covering: a
      `get_storage_client()`-wrapped read/write helper pair (so no future script can reinvent the
      `upload_from_string` mistake the sibling issue doc found), a standard `--dry-run`/`--apply`/
      `--confirm-prod-write` argparse scaffold, and a standard logging setup. **Not** the same thing as
      `market-tick-data-service/scripts/migration_common.py` (that file is domain-specific CeFi-v2 classification
      logic, `LEGACY_CHAIN_DATA_TYPES`/`classify_legacy_symbol` — stays local to MTDS as-is; only the truly generic
      scaffolding pieces belong in the new shared lib). This lib is also what every Phase 0b template imports —
      build it first, the templates depend on it. Done-when: at least the Phase 0 proof-of-concept move (prior
      todo) sources this lib, `bash scripts/quality-gates.sh` green.
- [ ] [INFRA] P2. Stamp/verify the 3-line lifecycle marker (`# Epic:`/`# Lifecycle:`/`# Delete-when:`, per
      `/codex/06-coding-standards/script-homes.md`) on every script moved in this plan — the two mega-repo source
      files already carry it (98% adoption, confirmed above); deployment-service's own 6 files already carry it too;
      verify it survives the `git mv`, don't silently strip it.

---

## Phase 0b — build canonical, parameterizable templates for the 5 recurring patterns (NEW, 2026-08-18 revision)

This is the actual deliverable the operator's 2026-08-18 pushback is asking for — distinct from, and more valuable
than, relocating existing dead one-off files (which Phases 1-3 still do where it's cheap or already-triaged, but
that is not the point of THIS phase). Each template lives under
`deployment-service/scripts/migrations/lib/templates/`, imports Phase 0's `migration_common.py` scaffolding
(storage client wrapper, `--dry-run`/`--apply`/`--confirm-prod-write` argparse baseline, logging) rather than
duplicating it, and exposes a small number of shape-specific parameterization hook points (a filter/predicate
function, a transform function, a target-path/bucket resolver) that the NEXT similar need fills in rather than
reinventing the whole script from scratch. Building 5 templates — not relocating 619 individual files — is the
actual leverage point §Pattern clustering's evidence points to.

- [ ] [INFRA] P1. `template_purge.py` (cluster 1 — row-removal/purge, 110 files' worth of precedent). Parameterizes:
      a row-selection predicate (criteria for "stale"/"phantom"/"duplicate"), an optional pre-delete backup-snapshot
      write (the exact write path the sibling issue doc found broken in 15 instruments-service files — this
      template's snapshot helper goes through `migration_common.py`'s `upload_bytes` wrapper so that specific bug
      class cannot recur), and a manifest-index update. Build against 1-2 of the Phase 1 files
      (`purge_bad_prediction_manifest_rows.py`, `purge_pre_launch_manifest_rows.py`) as the worked example — adapt
      those into the template rather than writing the template in the abstract first. Done-when: template exists,
      at least 1 Phase-1 file is refactored to import/parameterize it (not copy-pasted), `bash deployment-service/
      scripts/quality-gates.sh` green.
- [ ] [INFRA] P1. `template_canonicalize.py` (cluster 2 — field/path canonicalization & schema migration, the
      LARGEST cluster at 170 files' worth of precedent). Parameterizes: an old-shape → new-shape row transform
      function, a path-rewrite rule (old canonical-path segment → new), and a verification pass (old shape absent,
      new shape present, row counts reconcile). Build against `canonicalize_defi_manifest_venue_2026_06_14.py` (an
      instruments-service Phase-3 target) as the worked example. Done-when: same bar as above.
- [ ] [INFRA] P2. `template_reconcile.py` (cluster 3 — drift reconciliation & repair, 66 files' worth of precedent).
      Parameterizes: a two-source comparison function (manifest vs. GCS, or manifest vs. a derived-truth
      recomputation), a per-mismatch corrective-write function, and a mismatch-count report. Build against
      `reconcile_phantom_manifest_rows.py` (instruments-service Phase-3 target) as the worked example. Done-when:
      same bar as above.
- [ ] [INFRA] P2. `template_backfill.py` (cluster 4 — backfill/populate missing value, 108 files' worth of
      precedent). Parameterizes: a "needs backfill" row predicate, a value-computation function, and an in-place
      write-back. Build against a Phase-2/3 target (`backfill_cefi_source_column.py`, market-tick-data-service) as
      the worked example. Done-when: same bar as above.
- [ ] [INFRA] P2. `template_audit.py` (cluster 5 — read-only audit/investigation/verification, 74 files' worth of
      precedent — structurally distinct from the other 4: no `--apply`/mutation path needed at all, just a scan +
      structured report). Parameterizes: a scan function and an output formatter (text/JSON/CSV). Build against
      `teams_coverage_census_2026_08_05.py` (instruments-service) as the worked example. Done-when: same bar as
      above.
- [ ] [DOC] P2. Add a "Template roster" table to `scripts/migrations/README.md` (the stub Phase 0's first todo
      creates) listing all 5 templates, the operation-shape each covers, and a one-line "when to use this one"
      guide — this is what a future script author actually reads before writing anything, so it needs to be
      genuinely usable, not just a changelog entry. Cross-reference from `migration-script-ssot.md` (Phase 4).

---

## Phase 1 — remediate the 16 already-triaged Category-1 GCS-bug files

Source: `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`'s fleet-wide
triage table (definitive, re-run + verified 2026-08-18) — 15 files/20 call sites in instruments-service, 1 file/2
call sites in strategy-service, all calling `.blob(path).upload_from_string(...)` on UTL's read-only
`GCSBlobHandle`, silently swallowed by a `getattr`/`callable()` guard. This phase is that issue doc's own deferred
Follow-up items 1+2, now scoped as real todos per the operator's dispatch-scope decision for this plan.

- [ ] [DATA] P0. For each of the 15 instruments-service Category-1 files (`scripts/dedupe_manifest_schema_drift.py`,
      `scripts/fix_prediction_manifest_and_gcs_2026_05_22.py`, `scripts/migrate_available_at_column.py`,
      `scripts/migrate_fixtures_split.py`, `scripts/migrate_local_sfi_to_canonical.py`,
      `scripts/migrate_sports_available_at_column.py`, `scripts/purge_bad_prediction_manifest_rows.py`,
      `scripts/purge_bitget_phantom_null_rows.py`, `scripts/purge_deprecated_etf_manifest_rows_2026_05_16.py`,
      `scripts/purge_pre_launch_manifest_rows.py`, `scripts/purge_prediction_other_group_rows.py`,
      `scripts/purge_sports_unknown_venue_manifest_rows_2026_08_05.py`,
      `scripts/reclassify_kalshi_other_historical.py`,
      `scripts/reconcile_attempted_failed_to_captured_2026_05_13.py`,
      `scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py`), apply the proven
      `upload_bytes`/`download_as_bytes` fix pattern (per `deployment-service/scripts/vm/wave_launcher.py` and the
      already-fixed `deployment_service/deployment/state.py`, `deployment-service@c16b1f1407`), including
      `purge_prediction_other_group_rows.py`'s third, DIFFERENT-shaped bug (top-level `client.list_blobs()` returning
      bare `BlobMetadata` with zero I/O methods — not the `.blob()`-sourced case the other 14 share). Done-when: each
      file's write path verified live against its real target bucket (write + independent read-back, same
      methodology the issue doc used for `state.py`), no remaining `.blob(...).upload_from_string(`/
      `.download_as_string(` call sites (`grep -c` = 0 across the 15 files).
- [ ] [DATA] P0. Fix the 1 strategy-service Category-1 file, `scripts/run_2yr_config_grid_backtest.py` (2 call
      sites, unguarded — currently an uncaught `AttributeError` crash, not a silent no-op, per the issue doc). Same
      fix pattern + live verification as above.
- [ ] [DATA] P0. **Data-correctness prerequisite** (issue doc Follow-up item 2, not yet resolved): for each of the
      16 files above, determine from its `# Delete-when:` marker + git history whether it has ALREADY run in
      production (most are dated `_2026_05_13`/`_2026_05_16`/`_2026_05_22`/`_2026_08_05` one-offs, per the issue
      doc's own finding). Where a file already ran: check whether its now-confirmed-broken
      `.upload_from_string()` call (a backup-snapshot or canonical-index write) means the ROW-level purge/migration
      logic succeeded while the safety-backup silently no-op'd — this is a genuine GCS/manifest-state-consistency
      question, separate from (and prerequisite to) treating the file as fixed. Done-when: each of the 16 files has
      an explicit verdict recorded (either "backup write confirmed present post-hoc" or "backup write genuinely
      lost, no downstream inconsistency because <reason>" or "downstream inconsistency found, filed as
      `plans/active/issues/<new-slug>_2026_08_18.md`").
- [ ] [INFRA] P1. For each of the 16 files: check its `# Lifecycle:`/`# Delete-when:` marker. If `Delete-when`'s
      condition is ALREADY satisfied (confirmed one-shot, already run + verified per the prior todo) — do NOT
      relocate; it is a straightforward archive/delete candidate under the existing script-homes.md discipline
      (delete once the data-correctness check above clears it). If `Delete-when` is still open (the script may run
      again, or a re-run is plausible) — relocate into
      `deployment-service/scripts/migrations/{instruments-service,strategy-service}/` per Phase 0's structure,
      sourcing the new `migration_common.py` scaffolding (and, where the shape fits, a Phase 0b template) where it
      fits without a disruptive rewrite. Done-when: every one of the 16 files has an explicit disposition
      (archived-in-place / relocated) recorded in this plan's Progress Log with the git commit.

---

## Phase 2 — small/medium repos: full relocation (volume is cheap, no scope-narrowing needed)

- [ ] [DATA] P2. **market-data-processing-service** (13 files, `scripts/backfill-prediction-candles.sh`,
      `scripts/backfill_candle_manifest.py`, `scripts/backfill_defi_dex_pool_swaps_source_correction.py`,
      `scripts/backfill_odds_horizon_bucket_missing_shards_2026_07_28.py`,
      `scripts/blast_radius_cefi_chain_bundle_timestamp_float_2026_08_14.py`,
      `scripts/close_odds_horizon_bucket_expected_unattempted_cells_2026_07_25.py`,
      `scripts/migrate_candle_canonical_2026_07.py`,
      `scripts/migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py`,
      `scripts/reclassify_odds_horizon_bucket_unresolvable_rows_2026_07_28.py`,
      `scripts/scope_processed_candles_instrument_type_uppercase_corpus_cefi_tradfi_prediction_2026_08_17.py`,
      `scripts/scope_processed_candles_pool_uppercase_corpus_2026_08_17.py`,
      `scripts/sports/restamp_sports_candle_venue_2026_08_03.py`,
      `scripts/survey_tradfi_quarantine_raw_source_2026_07_27.py`). For each: check `Delete-when` status first (same
      rule as Phase 1's last todo — already-satisfied one-offs archive in place, don't relocate dead weight);
      relocate the rest into `deployment-service/scripts/migrations/market-data-processing-service/`. Done-when:
      `bash market-data-processing-service/scripts/quality-gates.sh` AND `bash deployment-service/scripts/quality-
      gates.sh` both green, no dangling reference to the old paths.
- [ ] [DATA] P2. **features-service** (18 files — `scripts/backfill_feature_orphan_class_e.py` through
      `scripts/write_sports_smoke_test_provenance_note_2026_07_28.py`, full list in this plan's §Discovery grep
      output; also `scripts/sports/*` subdirectory entries). Same Delete-when-first triage + relocate to
      `deployment-service/scripts/migrations/features-service/`. Done-when: same green-QG + no-dangling-reference
      bar as above.
- [ ] [DATA] P3. **strategy-service remainder** (the 2 non-Category-1 matches — `scripts/
      backfill_strategy_instructions_orphan_class_e.py`, `scripts/migrate_clients_yaml_to_client_first.py` — the 3rd
      strategy-service match, `run_2yr_config_grid_backtest.py`, is already covered by Phase 1). Relocate to
      `deployment-service/scripts/migrations/strategy-service/`.
- [ ] [DATA] P3. **unified-trading-library** (2 files — `scripts/migrate_manifest_v8.py`, `scripts/
      check_consolidator_lock_orphan_status_2026_08_17.py`). Relocate to `deployment-service/scripts/migrations/
      unified-trading-library/`. Note: UTL is a dependency of every other service (per
      `/codex/04-architecture/tier-and-import-architecture.md`'s tier rules) — confirm neither script is itself
      imported by UTL's own package code (only invoked as a standalone CLI) before moving, `grep -rn` for
      `from scripts.migrate_manifest_v8\|import migrate_manifest_v8` across the UTL package.
- [ ] [DATA] P3. **client-reporting-api** (1 file — `scripts/backfill_history.py`). Relocate to `deployment-service/
      scripts/migrations/client-reporting-api/`.
- [ ] [DATA] P3. **deployment-api** (1 file — `scripts/cleanup_ghost_venue_manifest_rows.py`). Relocate to
      `deployment-service/scripts/migrations/deployment-api/`. Note the mild irony (deployment-api is
      deployment-service's own API sibling) — still worth moving for the same "one canonical registry" reason as
      every other repo, not exempted just because it's adjacent.
- [ ] [DATA] P3. **e2e-testing** (the 6 genuine GCS-migration files identified in §Discovery's exclusion note —
      `scripts/defi/migrate_legacy_twins_from_audit.py`, `scripts/defi/migrate_uniswap_v4_legacy_to_canonical.py`,
      `scripts/defi/copy_lst_yields_prd_to_canonical_2026_07_14.py`,
      `scripts/sports/migrate_sports_md_unmappable_to_canonical_2026_06_19.py`,
      `scripts/sports/delete_sports_legacy_twinned_2026_06_19.py`,
      `scripts/sports/verify_sports_md_unmappable_twins_2026_06_19.py` — explicitly NOT the `launch_*_vm.sh`/
      `setup-backfill-vm.sh` files in the same directories, those stay governed by launcher-script-ssot.md).
      Relocate to `deployment-service/scripts/migrations/e2e-testing/`.

---

## Phase 3 — mega-repos: the genuinely-recurring subset only (per §Scope decision)

- [ ] [DATA] P2. **instruments-service — 13 `permanent`/`campaign`-marked files** (the mechanically-identified
      recurring subset, per §Discovery): `scripts/backfill_completion_key_overlap_gate_2026_08_09.py`,
      `scripts/canonicalize_defi_manifest_data_types_2026_05_16.py`,
      `scripts/canonicalize_defi_manifest_data_types_option_g_2026_05_16.py`,
      `scripts/canonicalize_defi_manifest_venue_2026_06_14.py`,
      `scripts/canonicalize_lending_indices_data_type_2026_05_16.py`,
      `scripts/cumulative_drawdown_guard_2026_08_15.py`,
      `scripts/measure_cefi_catalogue_enumeration_gap_2026_07_23.py`, `scripts/reconcile_phantom_manifest_rows.py`,
      `scripts/reconcile_phantom_manifest_rows_all.py`,
      `scripts/refresh_sports_weather_player_values_league_coverage_2026_06_21.py`,
      `scripts/resolve_dex_pool_factory_addresses_2026_08_09.py`, `scripts/teams_coverage_census_2026_08_05.py`
      (13th is `scripts/migrations/__init__.py` itself, see next todo). Relocate each to `deployment-service/
      scripts/migrations/instruments-service/`, re-verifying its `Delete-when` is genuinely open (not stale) before
      moving — re-check via `git log -1 --format=%cs -- <script>` per script-homes.md's staleness-hint method.
- [ ] [INFRA] P2. instruments-service already has its own partial local attempt at this same idea —
      `instruments-service/scripts/migrations/` (a stub subdirectory: `__init__.py` + 2 files,
      `validate_defi_metadata_cohesion.py` + `verify_defi_metadata_forward.py`). Fold this INTO the fleet-wide
      canonical structure rather than leaving a second, competing "migrations" directory inside instruments-service
      — move both files to `deployment-service/scripts/migrations/instruments-service/`, delete the now-empty
      `instruments-service/scripts/migrations/` directory. Done-when: `grep -rn "scripts.migrations" instruments-
      service/` (import references) returns nothing outside test fixtures, `bash instruments-service/scripts/
      quality-gates.sh` green.
- [ ] [DATA] P2. **market-tick-data-service — ~30 `permanent`/`campaign`/`reusable-*`-marked files** (full list per
      §Discovery grep, representative subset: `scripts/backfill_cefi_source_column.py`,
      `scripts/backfill_defi_source_column.py`, `scripts/defi_chain_genesis_relabel_migration_2026_06_01.py`,
      `scripts/defi_object_path_canonicalisation_2026_06_01.py`, `scripts/migrate_dex_pool_columns.py`,
      `scripts/migrate_dex_swap_columns.py`, `scripts/migrate_legacy_solana_defi_to_canonical.py`,
      `scripts/migrate_tradfi_ohlcv_session_stamps.py`, `scripts/mtds_reconcile_partial_bundles.py`,
      `scripts/mtds_reconcile_partition_mismatch.py`, `scripts/reconcile_market_tick_manifest.py`,
      `scripts/one_offs/restamp_manifest_consolidator_2026_07_26.py`,
      `scripts/one_offs/verify_legacy_bucket_decommission_precondition.py` — re-derive the exact current full list
      at execution time via `grep -l '^# Lifecycle: \(permanent\|campaign\|reusable\)' market-tick-data-service/
      scripts/*.py market-tick-data-service/scripts/*/*.py`, since new ones may land between authoring and
      execution). Relocate each to `deployment-service/scripts/migrations/market-tick-data-service/`.
- [ ] [INFRA] P2. market-tick-data-service ALSO already has a local partial-canonicalization attempt: `scripts/
      one_offs/` (2 files, subset of the prior todo) AND `scripts/migration_common.py` (domain-specific CeFi-v2
      helper — per Phase 0, this stays local, it is NOT generic scaffolding). Fold `scripts/one_offs/`'s 2 files
      into the fleet-wide move (covered by the prior todo); leave `migration_common.py` where it is, but add a
      one-line comment cross-referencing the new `deployment-service/scripts/migrations/lib/migration_common.py`
      so a future reader isn't confused by the name collision between the two DIFFERENT `migration_common.py`
      files.
- [ ] [DOC] P2. **Record the disposition of the ~500 remaining `oneoff`-marked instruments-service + market-tick-
      data-service scripts explicitly** in this plan's Progress Log once Phases 0-3's other todos are done — NOT
      relocated individually (that narrow-scope judgment stands, confirmed by the operator), but explicitly note
      that this population was the raw material for Phase 0b's 5 canonical templates (§Pattern clustering), so a
      future reader sees a deliberate, followed-through scope call, not an abandoned audit. If the operator later
      wants the literal full file-relocation sweep too, that is a new, separate plan (~500-file bulk relocation
      across 2 repos) — do not fold it into this one after the fact.

---

## Phase 4 — the policy change itself (make it real for every FUTURE script)

- [ ] [DOC] P1. Author a new codex SSOT doc — filename `migration-script-ssot.md`, in the `05-infrastructure`
      category directory alongside `launcher-script-ssot.md` (no resolvable citation given here since the file does
      not exist until this todo creates it), mirroring
      `/codex/05-infrastructure/launcher-script-ssot.md`'s shape (why-this-rule-exists, scope table of what counts
      as a "migration script" vs. a service CLI subcommand vs. an e2e harness, the `scripts/migrations/{repo}/`
      naming convention, the `migration_common.py` scaffolding contract, Phase 0b's 5-template roster (what each
      covers, when to adapt one vs. write something genuinely new), the relationship to
      `/codex/06-coding-standards/script-homes.md`'s existing `Lifecycle`/`Delete-when` marker discipline, and a
      migration-status table modeled on launcher-script-ssot.md's own "Migration status" section). Cross-link the
      relationship to VM launchers explicitly: a HEAVY migration (full-corpus GCS walk, manifest rewrite, bulk
      rename) still needs a companion VM launcher under `scripts/vm/` per CLAUDE.md's "no heavy I/O on the
      operator's local machine" rule — the migration LOGIC lives in `scripts/migrations/`, the VM LAUNCH mechanism
      (if needed) stays a separate `scripts/vm/launch-*.sh` that invokes it, same separation-of-concerns
      script-homes.md already draws for launcher-vs-compute-logic. Done-when: doc exists with `authoritative_for`
      frontmatter set, cross-referenced from the next todo.
- [ ] [DOC] P1. **Correct** `/codex/06-coding-standards/script-homes.md`'s decision-tree item 4 (currently: "one-off,
      single-repo operation tied to that repo's internals ... → repo-level `scripts/`") — **this is not a
      documentation-drift fix, it is a default-behavior change**: per the operator's 2026-08-18 pushback, "write a
      fresh repo-local one-off, tag it `Lifecycle: oneoff`, let it self-delete" is the anti-pattern going forward
      for any RECURRING-SHAPED need (one that matches one of Phase 0b's 5 templates, or a future addition to that
      roster) — the canonical-template path (`deployment-service/scripts/migrations/`, adapt/parameterize a
      template) becomes the actual SANCTIONED DEFAULT for that case. The existing `Lifecycle`/`Delete-when`
      one-off-marker convention remains fully valid, but ONLY for genuinely one-of-a-kind, never-expected-to-recur
      scripts — not as the default for everything, which is what item 4 currently reads as. Add a dated correction
      banner (2026-08-18, this plan) rather than silently rewriting — the existing text is not WRONG as written for
      its original intent, it is being narrowed by a new operator ruling, and other agents currently cite it as
      live truth. Point item 4 at the new `migration-script-ssot.md` for the migration/backfill/repair/canonicalize/
      audit subset (i.e. anything Phase 0b's template roster covers or a future addition to it); keep the decision
      tree's items 1-3 (service CLI / deployment-service-for-launch / e2e-testing) untouched. Done-when: both docs
      cross-reference each other via `related:`, no contradiction remains between the two (re-read both after
      editing, per CLAUDE.md's "newly-written claim must not contradict... a fact the SAME doc already shows
      elsewhere" discipline), and the corrected item 4 text explicitly states the "canonical template = default,
      Lifecycle-marker one-off = exception for genuinely non-recurring work" framing, not just a pointer to the new
      doc.
- [ ] [DOC] P2. Update `/plans/epics/infrastructure_master.md`'s `related_plans:` list to add this plan's slug (the
      epic's own `repos:` frontmatter list is representative, not exhaustive — several of its existing
      `related_plans` entries already touch repos outside that list, e.g. cefi/defi/sports plans — so no `repos:`
      edit needed, just the `related_plans:` addition, a single-line append).

---

## Phase 5 — lower-priority cross-reference (not this plan's primary remediation)

- [ ] [DOC] P3. Cross-reference only, per the sibling issue doc's own prioritization ("lower urgency... batch with
      other coding-standard cleanup"): the direct `google.cloud.storage`/`boto3` import census beyond the issue
      doc's specific `upload_from_string`/`download_as_string` grep found MORE Category-2-shaped files than that
      doc's 13 — `market-tick-data-service/scripts/` alone has 22 files importing `google.cloud.storage`/`boto3`
      directly (vs. the issue doc's 5 MTDS entries, which were scoped to the specific broken-method-name grep only).
      Do not fix these here — file a follow-up census as its own issue doc if/when
      `repo_scripts_governance_audit_2026_06_18.md`'s ruff-lint pass is ready to absorb it (that plan already owns
      the "raw SDK import" coding-standard angle); this todo is a pointer, not new remediation work.

---

## Progress Log

- **2026-08-18 (authoring session)**: Plan authored per operator directive (verbatim quote in `source:`). Real
  fleet discovery run against the live tree (not a placeholder): ~628 migration-shaped scripts across 11 repos
  outside deployment-service, ~98% Lifecycle-marker adoption in the two mega-repos (instruments-service,
  market-tick-data-service) enabling a mostly-mechanical one-shot-vs-recurring split. Confirmed deployment-service's
  own 6 existing migration scripts already use the correct `get_storage_client()`/`upload_bytes` pattern (no bug)
  but sit flat in `scripts/` root with no dedicated `scripts/migrations/` subdirectory (the Phase 0 gap). Found TWO
  repos (instruments-service, market-tick-data-service) already independently attempting local partial
  canonicalization (`scripts/migrations/` stub, `scripts/one_offs/` + `migration_common.py` respectively) —
  concrete evidence the operator's "we do this a lot" framing is correct, currently solved inconsistently
  per-repo. Explicit scope-narrowing flagged in §Scope decision (leave ~500 already-`oneoff`-marked scripts in
  place rather than force-relocating a working TEMPORARY-by-design population) — needs operator confirmation at
  plan review, not silently assumed as final.
- **2026-08-18 (revision session, different agent instance)**: Operator reviewed the authoring session's scope
  decision, confirmed "keep narrow scope" for the file-relocation question, but pushed back sharply on the framing
  of the ~500-file `oneoff` population (verbatim pushback quoted in `source:`, relayed via coordinator): leaving
  those files in place must not mean treating the audit as closed/ignored, because even a self-deleting one-shot
  script implements a reusable SHAPE the fleet keeps reinventing under today's "hacky" repo-local-one-off default.
  This session is a DIFFERENT agent instance than the authoring session (dispatched for an unrelated deployment-
  service task, with the plan-revision request relayed mid-task) — per the operator's own instruction to
  re-verify rather than trust the prior summary blindly, independently re-derived the fleet population fresh rather
  than reusing the authoring session's counts, and caught a real bug in the first re-derivation attempt (a
  double-path-prefix `sed` bug that silently zeroed every structural `grep -l` check — caught because the result
  was implausible, not accepted at face value). Corrected population: 619 files (not the ~628 the plan started
  with). Added real structural-signature evidence (83% already hand-roll argparse, 70% dry-run, 75%
  `get_storage_client()`, 65% `--confirm`/`--apply`, 99% `# Lifecycle:` marker) and a 5-cluster operation-shape
  breakdown (row-removal/purge 110, canonicalization/schema-migration 170, drift-reconciliation/repair 66,
  backfill/populate 108, read-only audit/investigation 74 — 528/619 = 85% cluster cleanly; the remaining 91 were
  sample-inspected, 20-file random sample, and mostly turned out to be naming-variant synonyms of the same 5
  shapes rather than genuinely novel operations). Added new Phase 0b (6 todos: 5 canonical, parameterizable
  templates — `template_purge.py`, `template_canonicalize.py`, `template_reconcile.py`, `template_backfill.py`,
  `template_audit.py` — plus a README "Template roster" table) as the actual deliverable this revision adds.
  Reframed §Scope decision item 5, Phase 3's last todo, and Phase 4's script-homes.md correction todo so none of
  them read as "audit closed, ignore" — the ~619-file audit is now explicitly the raw material for template
  design, and Phase 4's script-homes.md correction now states the canonical-template path is the sanctioned
  DEFAULT for a new recurring-shaped need, with the Lifecycle/Delete-when marker convention valid only for
  genuinely one-of-a-kind, never-to-recur work (not the default for everything, which is how item 4 read before).
  Bumped `estimate_baseline_ai_days` 8→10.5 / `estimate_calibrated_ai_days` 6.4→8.4 to reflect the added Phase 0b
  scope. `status` stays `active`; this revision does not change the operator-confirmation-needed status of the
  remaining file-relocation-scope question (§Scope decision), only sharpens what "leave in place" means for the
  ~500-file population.
