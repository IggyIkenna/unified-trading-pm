---
doc_type: issue
title:
  "cefi_migration_cutover_and_track8_completion todo 2 (:PERP:->:PERPETUAL: on-disk GCS rename) has a self-invalidating
  done-when check, no vetted VM launcher, and lands right after a sibling fleet showed 21/44 shards failing"
summary: >-
  Investigated (read-only, no execution) before dispatching todo 2 of
  cefi_migration_cutover_and_track8_completion_2026_07_25.md — the on-disk GCS filename rename for `:PERP:` ->
  `:PERPETUAL:` (Script 2, market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py). Three
  compounding concerns, none individually fatal but together enough to stop short of executing interactively: (1) the
  todo's stated done-when — a fresh run of scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py showing 0
  :PERP:-form rows — reads the AVAILABILITY MANIFEST, not GCS object filenames; the manifest side was already fixed by
  Script 3 (instruments-service@555ddf1c, 374,227/374,272 rows), so that check will almost certainly already read 0
  today regardless of whether Script 2's on-disk rename runs at all. The stated verification does not prove the thing
  the todo claims to prove. (2) No existing VM launcher wraps Script 2 — prior KRAKEN-SPOT/DERIBIT runs used an ad hoc
  dirty-tarball + custom VM_MIGRATION_CMD metadata override, not a registered launch-*.sh script; the workspace's
  unconditional heavy-I/O rule (>few-hundred-object renames must run on a VM in-region, never interactively) means
  proper execution requires building that launch path first, not reusing a vetted one. (3) A sibling migration fleet for
  the SAME cefi canonicalisation effort (Script 1's content-column --apply, 44 shards) was found one day earlier
  (cefi_content_migration_fleet_half_incomplete_2026_07_26.md, still open) to have only 23/44 shards reach the terminal
  completion banner — 21/44 died mid-run — contradicting an earlier "74/74 shards ALL_DONE" claim elsewhere in the
  execution log that this todo's own "self-justified, proven safe in production" framing leans on. Given the scale
  (candidate count likely in the hundreds of thousands, KRAKEN-SPOT precedent ran ~9.5h wall-clock for ~155,872 renames)
  and that this is a one-pass copy-then-delete GCS mutation, executing it live in an interactive session against an
  unverified done-when and an unreconciled sibling-fleet health question was judged too risky to do without first fixing
  the done-when check and re-verifying corpus GCS-filename state (not just manifest state).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, cefi, migration, gcs-rename, done-when-flaw, vm-launcher-gap, operator-notify]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: cefi_master
source: >-
  data_engineering-craft investigation of cefi_migration_cutover_and_track8_completion_2026_07_25.md todo 2, dispatched
  to slot 8 via /heartbeat "resume" 2026-07-27, before any GCS mutation was attempted. No commit landed against the
  target repos; this doc is the sole output of the investigation.
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# cefi `:PERP:` rename todo — done-when doesn't prove GCS state, no launcher, unreconciled sibling-fleet health

> **🟡 Needs an operator/data_engineering follow-up before todo 2 dispatches again** — not a hard-stop on the
> migration's safety per se (the underlying `resolve_canonical` pattern is proven, per KRAKEN-SPOT), but the
> _verification_ this specific todo names is broken, and it should not be treated as satisfied by a manifest-only green
> check.

## 1. The done-when check doesn't test what it claims to

Todo 2's stated done-when: "a fresh run of `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` shows 0
`:PERP:`-form instrument_id rows remaining in the live cefi manifest/GCS content."

`audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` reads `read_availability_index(cefi_bucket)` — the
**manifest**, via its `nc:perp_shorthand` classification bucket. The manifest-side rewrite already shipped
(`instruments-service@555ddf1c`, Script 3, 374,227/374,272 rows, per
`cefi_4surface_migration_execution_log_history_part1_2026_07_24.md:165-178`, "MIGRATION 1/3 APPLIED + DURABLE"). So this
audit almost certainly **already reads 0 today**, independent of whether Script 2 (the on-disk GCS filename rename,
`market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py`) has ever run for this venue
set. Running the audit and seeing 0 would look like "done" while proving nothing about GCS object filenames — the actual
thing todo 2 exists to fix.

**Suggested fix (not performed here)**: replace/augment the done-when with a live GCS listing check (or Script 2's own
`--dry-run` summary showing 0 planned renames — which the todo's second done-when clause already asks for, and is the
one clause that DOES prove the right thing). Consider dropping the audit-script clause entirely, or scoping it
explicitly to "confirms the pre-existing manifest fix, not a proxy for the GCS-rename outcome."

## 2. No vetted VM launcher for Script 2

Per the workspace's unconditional heavy-I/O rule, execution of Script 2 at its expected scale must run on a VM, not
interactively. Neither `deployment-service/scripts/vm/launch-cefi-migration-vm.sh` (hardcoded to
`migrate_cefi_instrument_types.py`) nor `launch-canonical-migration-vm.sh`'s `cefi` category (maps to
`migrate_cefi_flat_to_v9_canonical`) wraps Script 2. The KRAKEN-SPOT/DERIBIT precedents this todo cites as its safety
justification were run via an ad hoc dirty-tarball + custom `VM_MIGRATION_CMD` metadata override, not a reusable
launcher — so "reuses the already-dry-run-validated pattern" is true of the RENAME LOGIC, not of the deployment
mechanism. Building/extending a launcher is itself nontrivial scoped work, not a same-todo detail.

## 3. Unreconciled sibling-fleet health

`cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (P1, open, filed 2026-07-26 — one day before this
investigation) found Script 1's content-column `--apply` fleet (44 shards) only reached 23/44 terminal completion; 21/44
died mid-run (1.2%-99.9% progress, several SIGKILLed). This directly contradicts an earlier "74/74 shards ALL_DONE"
narrative for what may be the same or an adjacent fleet elsewhere in
`cefi_4surface_migration_execution_log_2026_07_24.md`. The two accounts are not reconciled in the docs. This doesn't
block Script 2 mechanically (it resolves target filenames via the catalogue, not by reading each object's own content
column) — but it undermines confidence that this migration effort's "done" claims are currently reliable, which matters
for a todo whose own safety argument leans on "prior renames were proven safe in production."

## Recommendation

Before todo 2 is dispatched again: (a) fix or rescope the done-when to actually test GCS filename state, (b) confirm or
reconcile the Script-1 fleet completion count against `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`, (c)
decide/build the VM launch path for Script 2 as its own scoped step (or extend an existing launcher) before an `--apply`
run is attempted. None of this was executed here — no GCS mutation, no VM launch, no code change; this doc is the entire
output of the investigation.
