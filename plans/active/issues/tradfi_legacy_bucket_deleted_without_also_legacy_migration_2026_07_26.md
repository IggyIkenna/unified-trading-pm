---
doc_type: issue
title:
  "R1 runbook violation: the legacy no-env market-data-tick-tradfi bucket (2,008-day corpus) was permanently deleted
  2026-07-06 WITHOUT the required --also-legacy migration ever completing — the one attempt that used the flag
  (2026-06-29) OOM-crashed after copying ~1% (37k/3.8M processed_candles), and the actual completing 2026-07-06 apply's
  launcher command never passes --also-legacy at all"
summary: >-
  `data_completion_tradfi_2026_07_15.md`'s R1 runbook item (line 298) requires `migrate_tradfi_to_v9_canonical --apply`
  to include `--also-legacy` before the legacy bucket is decommissioned, so the 2,008-day no-env corpus gets copied into
  canonical form first. E7 (line 180-183) reports the legacy bucket WAS permanently deleted 2026-07-06, "DONE — apply
  2026-07-06 exit_code=0/fatal=0". Code + doc audit (2026-07-26) finds: (1) the launcher command that actually ran that
  day (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` @ commit 77cfcda, the commit live at apply time)
  builds the tradfi invocation as `--start-date $START_DATE --end-date $END_DATE --workers ${WORKERS:-24}` — NO
  `--also-legacy` anywhere, and the flag's own `argparse` default is `action="store_true"` (False) with no launcher env
  knob to inject it; (2) the ONE prior attempt that DID use `--also-legacy`
  (`canonical-migration-tradfi-20260629-053023`, per `master_data_canonicalisation_migration_catalogue_2026_06_07.md`
  line ~303) OOM-crashed at 06:02 UTC after copying only ~37k of ~3.8M planned `processed_candles` objects (~1%), was
  never resumed with the flag, and the 2026-07-06 "DONE" apply is a SEPARATE, later run using the non-also-legacy
  launcher; (3) the legacy bucket (`market-data-tick-tradfi-central-element-323112`) is confirmed permanently deleted
  (`bucket.exists() == False` via ADC, ADC has active read creds). Net: at most ~1% of the legacy corpus was ever copied
  to canonical before the bucket holding the rest was destroyed.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, data-loss, legacy-migration, also-legacy, gcs-delete, governance, R1-runbook]
related:
  [
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
priority: P0
parent_epic: mtds_mdps_master
source:
  "slot 6, data_engineering, 2026-07-26, executing tradfi_satellite_ao_dispatch_batch3-002 (Audit R1/R2
  legacy-decommission safety)"
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

# TradFi legacy bucket deleted without the required --also-legacy migration — potential historical data loss

## What I found

**R1's requirement (line 298 of `data_completion_tradfi_2026_07_15.md`):** the v9 canonical `--apply` MUST include
`--also-legacy` to cover the 2,008-day no-env `market-data-tick-tradfi` corpus before that bucket is decommissioned —
"Without the flag, 2,008 legacy days orphan."

**E7's claim (line 180-183, same doc):** "hand C-GREEN to L6 → delete legacy `market-data-tick-tradfi` permanently...
DONE — apply 2026-07-06 exit_code=0/fatal=0."

**Evidence the flag was never actually used on the completing run:**

1. `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` at commit `77cfcda` (the version live on 2026-07-06,
   confirmed via `git log --before="2026-07-06T16:00:00" -1`) builds the tradfi invocation at line 93:
   `python -u -m market_tick_data_service.scripts.migrate_tradfi_to_v9_canonical --start-date $START_DATE --end-date $END_DATE --workers ${WORKERS:-24}`
   — no `--also-legacy` token anywhere in `_script_for`/`_launch`, and no env var in the whole script injects it.
2. `migrate_tradfi_to_v9_canonical.py`'s `--also-legacy` is `action="store_true"` — omitted means `False`, and
   `sources = [canon] + ([legacy] if args.also_legacy else [])` means the legacy bucket is SKIPPED entirely without it.
3. The completing 2026-07-06 apply ran via 2 VMs matching this launcher's naming convention:
   `canonical-migration-tradfi-20260706-145606` (2026 range, `planned=332825 moved=122703`, genuine work) and
   `canonical-migration-tradfi-20260706-152937` (historical range, `planned=1479669 moved=11` — near-total
   idempotent-skip, meaning that range's data was ALREADY canonical-shaped going in, from `canon`-source normalization,
   not from a legacy-bucket copy). Neither VM's run.log survives (rotated, >20 days old) to directly confirm
   `also_legacy=False` in the startup log line, but the launcher SOURCE at that exact commit is unambiguous.
4. **The one prior attempt that DID pass `--also-legacy`**:
   `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (line ~301-303) records "Operator fires `--apply`
   (`--also-legacy` per R1)" → VM `canonical-migration-tradfi-20260629-053023` launched 05:53 UTC 2026-06-29 → "🔴
   BLOCKED 2026-06-29: ... log stalled at 06:02 (SSL `UNEXPECTED_EOF` + connection-pool-full warnings); no EXIT_STATUS
   written; ~37k/3.8M processed_candles migrated (~1%); serial console shows continuous memory pressure ... (OOM-kill
   suspected)." The same doc explicitly says "OPERATOR ACTION REQUIRED: restart TradFi migration" — I find no evidence
   anywhere in the corpus that this restart ever happened WITH `--also-legacy` re-attached; the 2026-07-06 "DONE" apply
   is a distinct, later, non-also-legacy run per (1)-(3) above.
5. **The legacy bucket is confirmed gone**:
   `google.cloud.storage.Client().bucket("market-data-tick-tradfi-central- element-323112").exists()` returns `False`
   via ADC (live credential, not the poisoned CLI active-account) — permanent deletion is real, not a stale doc claim.

**Net**: at most ~1% of the legacy corpus (the partial 2026-06-29 OOM run, IF that partial write actually landed in
canonical before the crash — unverified) was ever copied to canonical form. The remaining ~99% of the 2,008-day legacy
corpus's objects, if they held anything not otherwise captured via the canonical bucket's own independent Databento
ingestion for the same range, are now unrecoverable — the bucket itself is gone, not just the R1 migration step skipped.

## R2 audit (bundled into the same todo, unrelated verdict)

Read-only GCS listing (ADC, no deletes) of the 3 still-unconfirmed R2 DELETE-AFTER targets in the CURRENT canonical
buckets:

| Target                                                         | Bucket                             | Result                                  |
| -------------------------------------------------------------- | ---------------------------------- | --------------------------------------- |
| bare `day=*/asset_group=tradfi/` without `pipeline_mode=`      | `market-data-tick-tradfi-prd-...`  | **0 objects** — clean                   |
| old-shape `processed_candles/` (no `pipeline_mode=` partition) | `market-data-tick-tradfi-prd-...`  | **0 objects** in a 50,000-object sample |
| instruments-store E6 bare `day=` paths                         | `instruments-store-tradfi-prd-...` | **0 objects** — clean                   |

R2 is CLEAN — nothing further to delete for these 3 targets, no operator-gated delete needed on this pass. ("the whole
legacy bucket," R2's 4th listed target, was already destroyed via E7 — see the finding above, not a clean R2 outcome.)

## Why it matters

This is the exact scenario CLAUDE.md's data-pipeline-correctness HARD RULE and the R1 runbook item were written to
prevent: an irreversible GCS delete (E7's own text calls it "⚠️ IRREVERSIBLE") ran without its stated precondition being
met. Whether this is SUBSTANTIVELY a real data-loss event (vs a procedural miss with no net loss, if the canonical
bucket's independent Databento backfill already covers the same 2020-2025ish range with equal or better fidelity) is NOT
something I can determine from the legacy bucket alone — it no longer exists to inspect. This is squarely the "big
finding" class (data-correctness, irreversible delete, governance HARD RULE) that requires operator notification, not a
todo I can close myself.

## Recommended decision

- [ ] [OPERATOR] P0. **Decide whether this needs remediation and how**, informed by: (a) does the canonical
      `market-data-tick-tradfi-prd` bucket's OWN Databento-sourced coverage for the legacy bucket's date range (2,008
      days — likely ~2018-2023 given the v9 apply covered "2020-2025 + 2026" separately, but the exact legacy range
      needs confirming from whatever pre-deletion inventory exists, e.g. a stale manifest snapshot or the migrator's own
      dry-run planned-count from BEFORE 2026-06-29) already have equivalent fidelity — if yes, this is a
      procedural-miss-with-no-net-loss and can close as such with that evidence cited; if the legacy bucket held
      anything genuinely unique (a different source, a wider date range, or higher-resolution ticks Databento's backfill
      doesn't reach), that data is gone. (b) Check whether GCS soft-delete / Object Versioning was enabled on this
      bucket (a short recovery window may still be open depending on how recently "permanent" deletion actually ran — I
      could not check this without `storage.buckets.get`, which none of my available credentials have).
- [ ] [SCRIPT] P2. Fix `data_completion_tradfi_2026_07_15.md` lines 298/304 (R1/R2 checkboxes) — R1 stays open pending
      the operator decision above (do not flip to done); R2 flips to done citing this doc's clean 3-target inventory.
- [ ] [SCRIPT] P3. Add a pre-delete GATE to `launch-canonical-migration-vm.sh` (or the runbook that invokes it) so a
      legacy-bucket-decommission step structurally CANNOT proceed without first verifying `also_legacy=True` appeared in
      a completed, non-crashed migration run for the same asset_group — this exact silent-gap class (a documented
      runbook precondition that a LATER, different invocation quietly doesn't satisfy) shouldn't require a manual
      forensic audit to catch after the fact.

## Codex SSOTs

`/codex/02-data/data-pipeline-correctness-hard-rule.md` (the rule this may violate),
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (the delete-safety procedure R1/E7 were supposed to follow).
