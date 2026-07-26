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

**Main's ruling on BLK-fd0758fb (2026-07-26): Option A — treat as a confirmed data-loss RISK, do NOT accept "procedural
miss, no net loss" unverified.** "Procedural miss, no net loss" is a claim that must be PROVEN with coverage evidence,
never assumed — an irreversible delete ran without its stated R1 precondition, exactly the class the
data-pipeline-correctness HARD RULE + `gcs-and-manifest-delete-safety-protocol.md` exist to catch. Split into what a
worker can do read-only now vs what is genuinely operator-gated:

- [ ] [DATA] P0. **Canonical coverage-equivalence census (worker-doable, read-only, NOT a full-corpus GCS walk)** —
      determine whether `market-data-tick-tradfi-prd`'s OWN Databento-sourced coverage already has equivalent fidelity
      for the legacy bucket's date range, via a MANIFEST CENSUS (deployment-api axis census / direct manifest read),
      never a whole-corpus GCS walk (heavy-I/O HARD RULE). Full canonical coverage of the same instrument × date range ⇒
      net loss ~0 (close as procedural-miss WITH this census evidence cited); any uncovered slice (wider date range /
      different source / higher-res ticks Databento can't reach) ⇒ that slice is the real, permanent loss. First bound
      the legacy range from surviving pre-deletion inventory (a stale manifest snapshot, or the migrator's
      pre-2026-06-29 dry-run planned-count ~3.8M processed_candles) — the deleted bucket itself can't be inspected, but
      what it HELD can still be scoped. Repo: market-tick-data-service / instruments-service.
- [ ] [OPERATOR] P0. **TIME-CRITICAL — GCS soft-delete / Object-Versioning recovery-window check.** Needs
      `storage.buckets.get` / `gcloud storage buckets list --soft-deleted`, which no available worker credential has.
      The bucket was deleted 2026-07-06 = 20 days ago as of this writing; GCS bucket soft-delete DEFAULT retention is 7
      days (configurable 7-90). If default, the restore window is ALREADY CLOSED; if a longer retention was configured,
      a SHRINKING window may remain. Check immediately — every day may close it permanently.
- [ ] [OPERATOR] P0. **The remediation decision itself** (restore the soft-deleted bucket if recoverable / re-run
      `migrate_tradfi_to_v9_canonical --apply --also-legacy` from a restored copy / accept the loss with the census
      evidence above) — prod-bucket-level infra, operator-only, gated on both items above.
- [x] ✅ [SCRIPT] P2. Fix `data_completion_tradfi_2026_07_15.md` lines 298/304 (R1/R2 checkboxes) — DONE (same session):
      R1 stays open pending the operator decision above; R2 flipped done citing this doc's clean 3-target inventory.
- [ ] [SCRIPT] P3. Add a pre-delete GATE to `launch-canonical-migration-vm.sh` (or the runbook that invokes it) so a
      legacy-bucket-decommission step structurally CANNOT proceed without first verifying `also_legacy=True` appeared in
      a completed, non-crashed migration run for the same asset_group — this exact silent-gap class (a documented
      runbook precondition that a LATER, different invocation quietly doesn't satisfy) shouldn't require a manual
      forensic audit to catch after the fact. **RE-SCOPE NEEDED (2026-07-26, see addendum below) — do not action as
      currently worded; the addendum's Option B is the concrete replacement scope.**

## 2026-07-26 addendum — todo 5 investigated, needs re-scoping before it's AO-actionable

Investigated where a "pre-delete gate" could concretely attach, per this todo's own two suggested locations
(`launch-canonical-migration-vm.sh` or "the runbook that invokes it"). Neither exists in the form the todo assumes:

1. **The named tool's launcher path is gone.** `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` no
   longer invokes `migrate_tradfi_to_v9_canonical.py` at all — `_script_for()`'s `tradfi` case was REPOINTED 2026-07-19
   to the newer orphan-proof content-migration chain (`migrate_tradfi_canonical_2026_07` →
   `rebundle_tradfi_chains_2026_07` → `recover_tradfi_garbage_underlying_2026_07`, built by
   `_tradfi_content_migration_cmd()`), per the launcher's own comment: "The old day-walking
   `migrate_tradfi_to_v9_canonical` is superseded." `migrate_tradfi_to_v9_canonical.py` still exists as a file but has
   no live launcher category pointing at it — adding a gate to the launcher's tradfi path would gate a code path that
   can no longer run, giving false confidence.
2. **The actual bucket decommission is a human-only hard stop, not a script's code path.** Per
   `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 hard stop #2 ("Any legacy-object delete after copy")
   - § 1 Part 5 (the legacy-COPIED-not-MOVED invariant, requiring 100% canonical-twin coverage before an asset_group's
     delete list executes), a legacy-bucket delete is NEVER agent-executed at any confidence level — E7's own text
     ("operator directly, interactive session") confirms the 2026-07-06 delete was a human running the delete outside
     any script's `--apply` path. There is no `--apply`/CLI invocation for THIS specific action to intercept — a code
     "gate" inside a launcher cannot structurally block a human typing a `gcloud storage buckets delete` command.
3. **No "runbook that invokes it" doc was found** as a distinct, editable target —
   `data_completion_tradfi_2026_07_15.md` states the R1 requirement in prose but isn't itself an executable gate, and no
   other runbook doc names a decommission-invoking script for the legacy tradfi bucket specifically.

**This makes the todo as literally worded not directly actionable** — it names a code location that can't enforce the
intended invariant. Recommending two options for whoever picks this up next (operator/main to choose, not decided here):

- **Option A (narrow, low-value)**: add a loud, structured warning to `migrate_tradfi_to_v9_canonical.py`'s own log
  output when `--apply` runs without `--also-legacy` (it already logs `also_legacy=%s` at the top, but that's a log
  line, not a durable artifact, and the tool isn't reachable via any current launcher — low value since nothing invokes
  it anymore).
- **Option B (general, actually closes the class this todo describes)**: build a small, STANDALONE, reusable
  pre-decommission verification CLI (e.g. `scripts/one_offs/verify_legacy_bucket_decommission_precondition.py` in
  market-tick-data-service) that operationalizes the ALREADY-DOCUMENTED Part 5 twin-coverage check from
  `gcs-and-manifest-delete-safety-protocol.md` as a runnable tool: given `--asset-group`/`--legacy-bucket`, it verifies
  canonical-twin coverage (via manifest census, not a full-corpus walk) for the legacy bucket's date range and exits
  non-zero with a clear failure report if coverage is incomplete. This becomes the "structural gate" a human
  decommission step is expected to run and paste evidence from FIRST — durable, greppable, reusable across asset_groups
  (not tradfi-specific, not dependent on which launcher/tool happens to be wired up this month). This is genuinely new
  tooling (not a location to bolt a check onto), so it deserves its own scoped follow-up plan/todo with a stated
  done-when, rather than continuing to live as this loosely-worded item.

**Recommendation: re-file this as a properly-scoped follow-up todo (Option B) in a new or existing plan, with an
explicit done-when** (e.g. "a unit test constructs a legacy bucket with a date range NOT fully covered in canonical and
asserts the tool exits non-zero with a clear report; a fully-covered case exits 0"). Declining to force either option
into this loosely-worded slot without that scoping — Option A is low-value on its own, and Option B is a real feature
that needs the same plan-authoring rigor (repo, done-when, estimate) as any other todo, not an ad-hoc implementation
under an audit-finding's addendum.

## Codex SSOTs

`/codex/02-data/data-pipeline-correctness-hard-rule.md` (the rule this may violate),
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (the delete-safety procedure R1/E7 were supposed to follow).
