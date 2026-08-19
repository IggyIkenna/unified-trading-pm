---
doc_type: codex-ssot
title: Migration script SSOT — `deployment-service/scripts/migrations/`
summary: "Every recurring-shaped one-off (purge/canonicalize/reconcile/backfill/audit — the 5 operation shapes
  found across ~619 repo-scattered migration scripts) belongs under deployment-service/scripts/migrations/{repo}/,
  parameterizing one of Phase 0b's 5 canonical templates rather than hand-rolling. Codifies the naming convention,
  the migration_common.py scaffolding contract, the template roster, the relationship to script-homes.md's
  Lifecycle/Delete-when marker discipline, and the VM-launcher split for heavy migrations."
status: current
nature: ssot
asset_group: [cross-cutting]
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
  ]
scope: [engineer]
tags: [scripts, migrations, script-homes, templates, lifecycle-marker, deployment-service]
related:
  [
    /codex/06-coding-standards/script-homes.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
  ]
created: 2026-08-19
authoritative_for:
  [migration-script placement decision, "scripts/migrations/{repo}/ naming convention", Phase 0b template roster]
referenced_by: [/codex/06-coding-standards/script-homes.md]
owner:
last_reviewed: 2026-08-19
code_refs: [deployment-service/scripts/migrations/]
last_reviewed_note: authored at plan completion, 2026-08-19; counts verified against the live tree same day
---

# Migration script SSOT — `deployment-service/scripts/migrations/`

**Codified 2026-08-19.** A fleet-wide census found ~619 migration-shaped scripts scattered across 11 repos' own
`scripts/` directories outside deployment-service — 85% of them cluster into exactly 5 recurring operation shapes
(purge, canonicalize, reconcile, backfill, audit). Every one of those was hand-rolled from scratch in its own
repo, re-solving the same read-manifest / mutate / write-back / verify scaffolding each time. This doc is the SSOT
for where a NEW migration script lives and how it gets built — mirroring
[`launcher-script-ssot.md`](launcher-script-ssot.md)'s shape for the analogous VM-launcher consolidation.

## Why this rule exists

1. **One canonical registry, not 11 competing local ones.** Two repos (instruments-service, market-tick-data-service)
   had already independently started their own partial `scripts/migrations/` stub directories before this SSOT
   existed — concrete evidence the underlying need ("we do this a lot") was already being felt, just solved
   inconsistently per-repo. A single `deployment-service/scripts/migrations/{repo}/` registry replaces every local
   attempt.
2. **The 5-cluster structure is real, not incidental.** Structural-signature evidence across all 619 files: 83%
   already hand-roll argparse, 70% support dry-run, 75% use `get_storage_client()`, 65% support `--confirm`/
   `--apply`, 99% carry a `# Lifecycle:` marker. The scaffolding was ALREADY converging on a shape by convention —
   this SSOT makes that shape a template instead of tribal knowledge.
3. **A canonical template closes the GCS-wrapper-bug class at the source.** The Category-1 `upload_from_string`/
   `.reload()`/`.generation`/`bucket.name` bug (a script calling a method that only exists on the native
   `google.cloud.storage.Blob`, not UTL's read-only `GCSBlobHandle` wrapper) recurred independently across at
   least 16 files this SSOT's founding plan fixed. A parameterized template that already routes correctly through
   `migration_common.py`'s wrapper calls can't reproduce that bug class in a NEW script the way a fresh hand-roll
   can.

## Scope: what counts as a "migration script" (vs. a CLI subcommand, vs. an e2e harness)

This is a NARROWING of [`script-homes.md`](../06-coding-standards/script-homes.md)'s decision-tree item 4
("one-off, single-repo operation") — not a new branch of the tree. If a script would land at item 4 AND its shape
matches one of the 5 clusters below, it now has a canonical home; item 4's `Lifecycle: oneoff`-and-self-delete
path stays valid only for genuinely one-of-a-kind work that matches none of them.

| Operation shape  | What it does                                                                                                                      | Canonical template         |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| **Purge**        | Read a manifest index, select rows to delete via a predicate, optional pre-delete snapshot, write back                            | `template_purge.py`        |
| **Canonicalize** | Rewrite a manifest column from a drifted old shape to a canonical new shape, optionally relocate path                             | `template_canonicalize.py` |
| **Reconcile**    | Compare a manifest row against a second source of truth (real GCS state, or a derived recomputation), correct only the mismatches | `template_reconcile.py`    |
| **Backfill**     | Flag rows missing a target value, derive the value from the row's own other columns, stamp in place                               | `template_backfill.py`     |
| **Audit**        | Read-only scan + structured report (census, coverage, investigation) — no mutation/`--apply` path at all                          | `template_audit.py`        |

**NOT this SSOT's scope** (stays under `script-homes.md`'s other decision-tree branches):

- Production runtime verbs (compute/fetch/validate/serve) → a service CLI subcommand, never a script at all.
- VM provisioning/launch/schedule → [`launcher-script-ssot.md`](launcher-script-ssot.md), `deployment-service/scripts/vm/`.
- Cross-repo / e2e / smoke-test orchestration → `e2e-testing/scripts/<domain>/`.
- A script whose logic is genuinely coupled to ONE repo's internal package (a hard `<repo>_service.*` import that
  would violate [tier-and-import-architecture.md](../04-architecture/tier-and-import-architecture.md)'s
  no-service-imports rule if relocated) — stays in its own repo's `scripts/`, `Lifecycle`-marked as usual. This is
  common enough to name explicitly: every relocation pass this SSOT's founding plan ran found several files
  blocked this exact way (a DEX-factory-registry resolver, a client-config-migration script, feature-orphan-sweep
  siblings) — it is not a failure of the template, it is the tier architecture doing its job.
- A script whose accompanying UNIT TEST hardcodes a same-repo relative path (`Path(__file__).resolve().parents[N]`)
  — relocating the script alone breaks the test; either move both together (script → `deployment-service/scripts/
migrations/{repo}/`, test → `deployment-service/tests/unit/`) in the SAME pass, or leave both in place until a
  pass has budget to move both.
- Live, load-bearing product code that a MATCHING FILENAME sweep can mis-flag as migration-shaped (e.g. a script a
  CLI subcommand dynamically imports at runtime) — always verify actual import/consumer coupling before relocating
  purely on a filename-pattern match; a `backfill_*.py` name does not guarantee migration-shaped content.

## The `scripts/migrations/{repo}/` naming convention

```
deployment-service/scripts/migrations/
├── lib/
│   ├── migration_common.py          # shared helpers: logging, arg-parsing, write-mode, download/upload wrappers
│   └── templates/
│       ├── template_purge.py
│       ├── template_canonicalize.py
│       ├── template_reconcile.py
│       ├── template_backfill.py
│       ├── template_audit.py
│       └── examples/                # one worked example per template
├── self/                            # deployment-service's own pre-existing migration scripts
├── instruments-service/             # relocated FROM instruments-service
├── market-tick-data-service/        # relocated FROM market-tick-data-service
├── market-data-processing-service/
├── features-service/
├── strategy-service/
├── unified-trading-library/
├── client-reporting-api/
├── deployment-api/
└── e2e-testing/
```

A relocated file keeps its original basename (no renaming as part of the move — a rename is a SEPARATE decision,
not bundled into a relocation). Corresponding unit tests land in `deployment-service/tests/unit/test_<name>.py`
alongside the script's own package layout, not in a `tests/migrations/` mirror subtree.

## The `migration_common.py` scaffolding contract

`deployment-service/scripts/migrations/lib/migration_common.py` provides the shared, repo-agnostic scaffolding
every template builds on:

| Function                               | Purpose                                                                      |
| -------------------------------------- | ---------------------------------------------------------------------------- |
| `configure_migration_logging()`        | Standard `logging.basicConfig` shape, consistent across every script         |
| `build_migration_arg_parser()`         | Shared argparse scaffold (`--dry-run`/`--apply`, `--bucket`, common flags)   |
| `resolve_write_mode()`                 | Resolves the effective write mode (`MigrationWriteMode` dataclass) from args |
| `download_bytes()` / `download_text()` | Read wrapper — routes through `get_storage_client()`, never a raw GCS client |
| `upload_bytes()` / `upload_text()`     | Write wrapper — same routing; the fix point for the Category-1 GCS bug class |

**Two repos already had their own LOCAL `migration_common.py` before this SSOT** — `market-tick-data-service/
scripts/migration_common.py` is a genuinely domain-specific CeFi-v2 helper (per Phase 0's own scoping decision, it
stays local, it is NOT generic scaffolding this SSOT's shared file replaces) and carries a cross-reference comment
distinguishing it from the fleet-wide one. If a future repo's local helper turns out to be genuinely generic
(not domain-coupled), fold it into the shared `lib/migration_common.py` instead of leaving a second copy.

## Template roster (Phase 0b, all 5 shipped 2026-08-18/19)

Full API + worked-example detail lives in `deployment-service/scripts/migrations/README.md`'s "Template roster"
table — read that before writing a new migration script, it is the actually-usable reference. Summary:

| Template                   | Parameterization hooks                                                                               | Built against (worked example)                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `template_purge.py`        | `predicate`, optional `snapshot_before_delete`, optional `manifest_index_updater`                    | `purge_pre_launch_manifest_rows.py`              |
| `template_canonicalize.py` | `transform` (old→new row rewrite), optional `path_rewrite`, optional `new_shape_predicate`           | `canonicalize_defi_manifest_venue_2026_06_14.py` |
| `template_reconcile.py`    | `comparator` (mismatch mask, may do its own GCS lookups), `corrective_write`, optional `group_by_fn` | `reconcile_phantom_manifest_rows.py`             |
| `template_backfill.py`     | `needs_backfill` (row predicate), `compute_value`, `target_column`                                   | `backfill_cefi_source_column.py`                 |
| `template_audit.py`        | `scan` (returns a structured report), optional `columns` projection                                  | `teams_coverage_census_2026_08_05.py`            |

**When to adapt a template vs. write something genuinely new**: if the operation is "read a manifest, do ONE of
the 5 things above to some rows, write back" — adapt the matching template. If it's genuinely novel (not a
variant of any of the 5 shapes — e.g. a one-time cross-repo data-format overhaul with no repeat precedent), a
fresh `Lifecycle: oneoff` script under the target repo's own `scripts/` remains valid per `script-homes.md`.

**Known gap (as of 2026-08-19, tracked not silently accepted)**: every template above was built as a standalone
worked example, not yet by refactoring a REAL shipped file to import/parameterize it — the real source file for
each template lived in a different repo than deployment-service at authoring time, out of that authoring pass's
own change scope. The done-when bar ("at least 1 real file imports the template") remains open for all 5; closes
naturally as more source-repo files get relocated in future passes and refactored to use their matching template
instead of hand-rolled logic.

## Relationship to `script-homes.md`'s Lifecycle/Delete-when marker discipline

Every relocated (or newly-written) migration script keeps its `# Epic:` / `# Lifecycle:` / `# Delete-when:`
3-line header — relocation does not change lifecycle classification. A script built from a template is typically
`campaign` (a phase-scoped need with a named milestone) rather than `permanent`; `oneoff` remains valid, but ONLY
under the tightened evidence-based criterion below.

**[`script-homes.md`](../06-coding-standards/script-homes.md)'s decision-tree item 4 is corrected** (dated banner,
same date as this doc) to point the migration/backfill/repair/canonicalize/audit subset here — the canonical
template path is now the sanctioned DEFAULT for that subset, not a same-weight alternative to a fresh hand-rolled
one-off. Read that doc's corrected item 4 for the full framing.

### `Lifecycle: oneoff` is correct for the SCRIPT, almost never for the SHAPE (2026-08-19 ruling)

**Default assumption, flipped**: don't assume a fresh migration/purge/canonicalize/reconcile/backfill/audit script
is a one-time thing just because THIS invocation's specific target (a specific venue, a specific date-stamped bug,
a specific bad manifest row) won't recur identically. Shard definitions, manifest names, and schema versions keep
changing — assume the OPERATION SHAPE will be needed again for a different target, because the fleet's own history
says it will be. Phase 0b's 5 templates exist BECAUSE ~528 of 619 audited scripts (85%) turned out to share just 5
shapes despite every one being hand-rolled as if it were a one-of-a-kind need.

**The actual test, derived from the 26 files this plan's own follow-up sweep confirmed safe to DELETE** (i.e.
genuinely, permanently dead — not "haven't needed it again yet"): every one of those 26 was scoped to a single,
now-PERMANENTLY-CLOSED condition — a specific date-stamped incident whose root cause is fixed at the source (so
the same bad data can never be produced again), a specific bucket that's since been deleted/decommissioned
entirely, or a specific historical vendor quirk tied to a dataset that no longer exists. None of them could recur
even in principle, because the thing that made them necessary is gone, not just currently quiet.

Contrast that with the ~500-file surviving population: those are ALSO individually one-time (each fixed one
specific incident), but the CONDITION CLASS that produced them — "a venue gets renamed," "a schema version bumps,"
"a new asset group onboards with its own data quirks" — is structurally ongoing. The next occurrence needs a new
script with the same shape, even though it won't literally be a re-run of the old one.

**So**: `Lifecycle: oneoff` for a purge/canonicalize/reconcile/backfill/audit-shaped script is correct ONLY when
the underlying CONDITION CLASS is itself closing permanently (the bucket goes away, the vendor relationship ends,
the schema freezes) — not merely because this specific instance is one-time. If in doubt, treat it as `campaign`
and build it via the matching template; the template import costs nothing extra and the scaffolding is right
either way. A script that turns out to have been genuinely one-of-a-kind is still trivially deletable later — a
script that turns out to have been the FIRST of a recurring pattern, hand-rolled as `oneoff`, is technical debt
the fleet has already paid for once (that's literally why this plan and its templates exist).

### Machine-enforced (QG STEP 5.109, 2026-08-19)

`check_oneoff_recurring_shape_ratchet.py` (wired into `base-service.sh`/`base-library.sh`, so every repo's own
`quality-gates.sh` runs it) flags any `scripts/` file — outside `deployment-service/scripts/migrations/`, the
canonical destination — whose basename matches the same operation-shape regex this plan's own §Discovery process
used (`migrat|backfill|repair|fix_|cleanup|clean_up|one_off|oneoff|_YYYY_MM_DD|reconcile|purge|wipe_|dedupe|
dedup_`) AND carries `# Lifecycle: oneoff`. This is a grep-based heuristic (filename pattern, not true semantic
shape detection) — the same acceptable shape `launcher-script-ssot.md`'s own governance checks use, with a
documented false-positive boundary, not a claim of perfect precision.

**Baseline-ratchet, not zero-tolerance**: `oneoff_recurring_shape_ratchet_baseline.yaml` grandfathers the day-1
legacy population (seeded 2026-08-19 at this plan's archival — the ~500-file surviving population plus every other
repo's own count) so the check lands green on introduction. A NEW file matching both conditions, not already in
the baseline, fails the gate — the author must either adapt the matching template or add `# QG-allow: <reason>` on
the `# Lifecycle:` line justifying why the name match is a false positive. The baseline only shrinks, ratcheted
DOWN as legacy files get individually resolved (relocated + wired to a template, or genuinely deleted per the
criterion above) — never raised.

## Relationship to VM launchers — heavy migrations still need a companion launcher

A migration script's LOGIC lives under `scripts/migrations/{repo}/` regardless of scale. But CLAUDE.md's "no heavy
I/O on the operator's local machine" rule is unchanged: a HEAVY migration (a full-corpus GCS walk, a manifest
rewrite touching many shards, a bulk rename) still needs a companion VM launcher under `scripts/vm/launch-*.sh`
per [`launcher-script-ssot.md`](launcher-script-ssot.md) — the migration script is what the VM runs, the launcher
is how it gets a VM to run on. Keep the separation of concerns launcher-script-ssot.md already draws between
launch mechanism and compute logic; do not fold migration logic INTO a launcher script, and do not skip the
launcher for a migration heavy enough to need one.

## Migration status (2026-08-19) — verified against the live tree

Founding plan: [`migration_script_canonicalization_into_deployment_service_2026_08_18.md`](/plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md).
Counts below are `.py` files present in each `deployment-service/scripts/migrations/{repo}/` subdirectory, verified
2026-08-19 (not the historical relocation-event counts, which differ slightly due to test-file and stub-directory
folding — see the plan's own Progress Log for the full per-file disposition of every relocation pass).

| Repo                              | Files relocated | Notable exclusions (left in place, reason)                                                                            |
| --------------------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------- |
| `instruments-service`             | 19              | 3 blocked (hard internal import ×2, sibling-script dynamic-load ×1)                                                   |
| `market-tick-data-service`        | 20              | 10 blocked (2 hard internal import, 4 test-coupling, 4 pending a GCS-wrapper fix before relocation)                   |
| `market-data-processing-service`  | 3               | 9 Delete-when-satisfied (archive-in-place), 1 blocked (hard internal import via subprocess)                           |
| `features-service`                | 1               | 4 Delete-when-satisfied, 14 blocked (8 hard import, 1 sibling dynamic-load, 1 monkeypatch, 3 subprocess-venv-coupled) |
| `e2e-testing`                     | 2               | 4 Delete-when-satisfied                                                                                               |
| `deployment-api`                  | 1               | —                                                                                                                     |
| `unified-trading-library`         | 1               | 1 Delete-when-satisfied                                                                                               |
| `strategy-service`                | 0               | 2 blocked (hard internal import ×1, sibling dynamic-load ×1) — both stay in place, not relocated                      |
| `client-reporting-api`            | 0               | 1 excluded — not migration-shaped despite filename match; live product code with CLI import dependencies              |
| `self` (deployment-service's own) | 6               | pre-existing, moved into the canonical structure at Phase 0                                                           |

**~500-file remaining population** (instruments-service + market-tick-data-service `oneoff`-marked scripts not
individually relocated): deliberately NOT relocated file-by-file — this was the raw material sampled/analyzed to
derive the 5-cluster operation-shape breakdown and build the template roster above. A literal full-population
relocation sweep, if ever wanted, needs its own separate plan.

## References

- [`launcher-script-ssot.md`](launcher-script-ssot.md) — the VM-launcher consolidation this doc's shape mirrors.
- [`script-homes.md`](../06-coding-standards/script-homes.md) — the parent decision tree; item 4 corrected same date.
- [`tier-and-import-architecture.md`](../04-architecture/tier-and-import-architecture.md) — the no-service-imports
  rule behind most "left in place, blocked" dispositions above.
- Founding plan (archived): `/plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md`.
