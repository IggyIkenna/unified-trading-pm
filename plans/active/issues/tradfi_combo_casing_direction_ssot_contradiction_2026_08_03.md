---
doc_type: issue
title:
  TradFi manifest `instrument_type` casing has TWO contradictory "resolved" migrations pulling the SAME 1.3M+ row
  population in OPPOSITE directions — 100%-UPPERCASE directive vs. an archived lowercase-relabel that already executed
summary: >-
  While working tradfi_casing_100pct_redrift-014 (re-run migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py
  --apply, gated on the UTL seam shipping + all writer fleets redeploying — both confirmed done), a dry-run found
  1,400,429 candidate rows, ~17x the plan's last-documented 82,311 residual and past the script's own STOP-ON-SURPRISE
  ceiling (500,000) — it correctly refused rather than blindly rewrite. Diagnosis: NOT a new writer bug. A SEPARATE,
  already-archived-as-resolved issue
  (plans/archive/issues/tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md, instruments-service@f3cd7dd1,
  applied live 2026-07-29) mass-relabeled 1,314,705 UPPERCASE `COMBO` rows to LOWERCASE `combo` — the EXACT OPPOSITE
  direction of the 100%-UPPERCASE directive this issue thread exists to enforce. Live re-read today shows ~1,339,466
  tradfi combo-lowercase rows, matching that migration's 2026-07-29 post-apply total (1,339,306) plus organic growth.
  Re-running the UPPERCASE script now would flip these same 1.3M+ rows a THIRD time with no coordination between the two
  efforts. NOT executed — escalating instead.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [tradfi, casing, instrument-type, manifest, ssot-contradiction, combo, data-correctness]
related:
  [
    /plans/active/issues/tradfi_casing_100pct_redrift_2026_07_27.md,
    /plans/archive/issues/tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md,
    /plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
priority: P0
parent_epic: tradfi_master
assigned_vm: planning
source: [tradfi_casing_100pct_redrift_2026_07_27.md]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: investigate
depends_on: []
---

## What I found

Executing `tradfi_casing_100pct_redrift-014`'s todo (re-run
`migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` — gated on the UTL seam shipping AND all writer
fleets redeploying; both prerequisites independently verified this session: UTL `688e49bc` confirmed content-present at
the currently-deployed `v0.72.0` tag despite the squash-merge non-ancestry false-negative — see `review.md`'s
squash-merge caveat; all three writer images (market-tick-data-service:latest, instruments-service:latest,
market-data-processing-service:latest) rebuilt 2026-08-03 from commits pinning `unified-trading-library>=0.72.0`;
`gcs_bucket_soft_delete_retention_seconds()` on the tradfi bucket returns 604800s, satisfying the reversibility-verified
no-`[OPERATOR]` path).

**Dry-run surprise**: 1,400,429 candidate rows would change (vs. this issue's last-documented 82,311 residual — a ~17x
jump), exceeding the script's own `_EXPECTED_CANDIDATE_MAX` STOP-ON-SURPRISE ceiling (500,000). The script correctly
refused rather than rewrite an uncharacterized population — `--apply` was NOT forced.

**Diagnosis — NOT an active writer regression.** `written_at` freshness on the dominant CME/ICE `combo`-lowercase
population (979,196 CME rows sampled) is 92% dated 2026-07-18 or earlier — predating every commit in this issue's own
remediation timeline. The manifest consolidator (`uts-prod-manifest-consolidator-market-data-tradfi`) runs continuously
on a ~1-minute cadence with no visible backlog-catchup gap, ruling out a simple "stale consolidator window" — the real
explanation is a SEPARATE, already-executed migration:

**`plans/archive/issues/tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md`** (archived `status: resolved`,
`resolved_by: instruments-service@f3cd7dd1 — migration applied live to prod 2026-07-29`) built and ran
`instruments-service/scripts/migrate_tradfi_combo_manifest_casing.py`, which relabeled **1,314,705 UPPERCASE `COMBO`
rows → LOWERCASE `combo`** (pre-migration census: `COMBO`=1,315,878 / `combo`=23,428; post-apply verified: `COMBO`=0,
`combo`=1,339,306 — exactly the pre-migration sum). That is the **EXACT OPPOSITE direction** of the 100%-UPPERCASE
directive (`plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) this issue thread
(`tradfi_casing_100pct_redrift_2026_07_27.md`) exists to enforce — and it ran 2 days AFTER this thread's own
`mtds@a1729bb4` had already fixed 23,428 of those same rows FROM lowercase TO uppercase (2026-07-27), silently reversing
that fix along with everything else.

Today's live re-read: ~1,339,466 tradfi-wide `combo`-lowercase rows — matching the 2026-07-29 migration's post-apply
total (1,339,306) plus ~160 rows of organic growth since. **This is that migration's aftermath, not a new bug**, and the
two issue threads never cross-referenced each other (confirmed via grep — neither doc names the other, and no
active-corpus doc names both).

## Why it matters — a genuine SSOT contradiction, not just a scale surprise

The two migrations disagree about which casing is canonical, and each was "resolved" using different anchors:

1. **UAC's own schema is UPPERCASE**: `unified_api_contracts/_instrument_enums.py:92` —
   `InstrumentType.COMBO = "COMBO"`. This is the actual SSOT enum member value.
2. **The archived 07-28/29 migration anchored instead to a WRITER convention**, not the schema:
   `instruments-service/scripts/enumerate_expected_universe.py::_canonical_writer_instrument_type` (line 1710) documents
   "MTDS writes captured cells at the CANONICAL BUNDLED grain LOWERCASE (`future`/`equity`/`etf`/`combo`/
   `futures_chain`/`options_chain`)" and is used (line 1938) to seed `expected_unattempted` placeholder rows so a later
   capture's shard atom matches the seed's. Its own docstring predates this issue thread's UTL-seam fix (2026-07-27,
   `unified-trading-library@688e49bc`), which now canonicalizes EVERY tradfi write to UPPERCASE additively at the shared
   `ManifestWriter` seam — meaning `_canonical_writer_instrument_type`'s lowercase assumption is now **STALE relative to
   the writer's actual current behavior**.
3. **Un-verified fallout risk**: if MTDS's writer now stamps UPPERCASE (via the UTL seam, confirmed shipped + redeployed
   fleet-wide) but `enumerate_expected_universe.py` still SEEDS `expected_unattempted` rows using
   `_canonical_writer_instrument_type`'s lowercase convention, the seed and the real capture no longer share the same
   shard atom — a seed can never convert to `captured` (permanently deflating honest-coverage for `combo` cells). This
   has NOT been verified either way in this session; it is a plausible NEW regression the 07-27 UTL-seam fix may have
   introduced for the seeding path, independent of which casing direction is "correct."

**Net**: re-running this issue's UPPERCASE script now would flip the same ~1.3M rows a THIRD time, with zero
coordination with the archived effort, and would not by itself resolve the seeding-staleness risk in (3). The population
size and STOP-ON-SURPRISE refusal are symptoms; the actual defect is that two independent "resolved" migrations disagree
about ground truth and neither checked the other or the real schema enum before executing a mass rewrite of live
production data.

## Recommended decision

1. **Casing direction**: UPPERCASE is very likely correct — it matches UAC's own enum definition (`COMBO = "COMBO"`) and
   this issue's already-shipped, operator-ruled UTL centralized canon (`canonicalize_manifest_instrument_type`,
   `unified-trading-library@688e49bc`). The archived 07-28/29 migration's lowercase direction appears to have been an
   error (anchored to a non-schema writer convention, not the SSOT enum) — but given it already executed once and this
   would be reversing it, this is an operator call, not something to execute unilaterally a third time.
2. **Before any re-apply**: verify whether `enumerate_expected_universe.py::_canonical_writer_instrument_type` is still
   seeding `expected_unattempted` rows in lowercase while the writer now captures in uppercase (the shard-atom mismatch
   risk in "Why it matters" #3) — if so, that seeding function needs updating to the UPPERCASE convention FIRST (or in
   the same pass), or every combo seed cell silently stops being convertible.
3. **Cross-reference discipline**: once resolved, this doc, the archived 07-28 doc, and the 07-24 100%-directive doc
   should all cross-reference each other so a THIRD reversal doesn't happen again unnoticed.
4. Once (1)+(2) are resolved, `tradfi_casing_100pct_redrift-014`'s `--apply` can proceed against the now-understood
   ~1.4M-row population (with the script's STOP-ON-SURPRISE ceiling raised to match, citing this diagnosis).

- [ ] [OPERATOR] P0. Decide the canonical casing direction for tradfi `combo` (and by extension every other
      instrument_type this affects) — UPPERCASE per UAC schema + the existing operator ruling in
      `tradfi_casing_100pct_redrift_2026_07_27.md`, or LOWERCASE per the archived 2026-07-29 migration's precedent. This
      gates every todo below. (repo: unified-trading-pm)
- [ ] [DATA] P1. Verify whether
      `instruments-service/scripts/enumerate_expected_universe.py::_canonical_writer_instrument_type` still seeds
      `expected_unattempted` rows in lowercase while MTDS's writer now captures in UPPERCASE (post
      `unified-trading-library@688e49bc`) — if confirmed, fix the seeding function to match the ruled-canonical casing
      so seed/capture shard atoms stay aligned. (repo: instruments-service)
- [ ] [DATA] P1. Once the direction is ruled + the seeding function (if broken) is fixed: re-run
      `market-tick-data-service/scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` (raising
      `_EXPECTED_CANDIDATE_MIN`/`_EXPECTED_CANDIDATE_MAX` to bracket the now-understood ~1.4M-row population) if
      UPPERCASE is ruled, OR write the equivalent lowercase-direction script update if LOWERCASE is ruled instead.
      (repo: market-tick-data-service)
- [ ] [DATA] P2. Cross-reference this doc, `tradfi_casing_100pct_redrift_2026_07_27.md`, and the archived
      `tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md` from each other so future casing work sees all
      three. (repo: unified-trading-pm)

## Progress Log

- 2026-08-03 (slot-7): filed after `tradfi_casing_100pct_redrift-014`'s dry-run surfaced the 17x population surprise;
  root-caused to the archived 07-28/29 lowercase migration via GCS backup-snapshot filenames
  (`_index/backups/availability_index.pre_combo_casing_relabel_2026072*`) cross-referenced to the archived issue's
  Progress Log. No code changed, no manifest write attempted.
