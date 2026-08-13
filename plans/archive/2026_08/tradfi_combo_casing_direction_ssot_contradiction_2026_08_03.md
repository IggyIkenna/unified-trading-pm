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
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [tradfi, casing, instrument-type, manifest, ssot-contradiction, combo, data-correctness]
related:
  [
    /plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md,
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
  "market-tick-data-service@4cae1cb0 (ceiling raise) + the real --apply, 2026-08-04 -- 6,600,032 rows rewritten,
  1,401,523 case-corrected, independently re-verified 0 residual"
locked_by:
execution_scope: orchestrator-agent
drift_direction: investigate
depends_on: []
# 2026-08-03 (slot-8): the 4 todos below are a REAL dependency chain, not
# independent parallel work -- -002/-003 both depend on the still-open P0
# casing-direction decision in -001, and -004 (cross-reference) only makes
# sense after -001..-003 close out. sequential=true wires
# prereqs.completed_tasks in plan_order so the dispatcher stops offering
# -002/-003 while -001 is still open (it already did once: -002 was
# dispatched and -003 was dispatched to slot-8, both while -001 sat
# status=blocked awaiting a human decision).
sequential: true
context_scope:
  [
    /plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md,
    /plans/archive/issues/tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md,
    unified-api-contracts/unified_api_contracts/_instrument_enums.py,
    instruments-service/scripts/enumerate_expected_universe.py,
    unified-trading-library/unified_trading_library/canonical/_manifest_instrument_type_canon.py,
    market-tick-data-service/scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py,
  ]
---

> **🟢 ARCHIVED 2026-08-04** — status=resolved, all four todos done. Direction ruled UPPERCASE (operator, Option A);
> seeding-function staleness fixed (`instruments-service@47a631ff`, `@d79b9d74`); the real `--apply` landed
> (`market-tick-data-service@4cae1cb0` ceiling raise + apply) — 6,600,032 rows rewritten, 1,401,523 case-corrected,
> independently re-verified 0 residual against the post-apply generation; cross-references added to the archived
> `tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md` and
> `cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`. Codex-alignment: added a new lesson to
> `/codex/02-data/availability-manifest-and-data-status.md` on seed/capture casing parity (a manifest-column casing
> canon must be applied identically at every place that materializes a row for the same shard atom, not just the writer
> seam). Archived per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s 6-step ritual.

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

- [x] ✅ [OPERATOR] P0. Decide the canonical casing direction for tradfi `combo` (and by extension every other
      instrument_type this affects) — UPPERCASE per UAC schema + the existing operator ruling in
      `tradfi_casing_100pct_redrift_2026_07_27.md`, or LOWERCASE per the archived 2026-07-29 migration's precedent. This
      gates every todo below. (repo: unified-trading-pm) — **RULED 2026-08-04 (direct operator confirmation, interactive
      session): UPPERCASE.** Matches UAC's `InstrumentType.COMBO = "COMBO"` schema enum and the existing operator ruling
      already on file in `tradfi_casing_100pct_redrift_2026_07_27.md`; the archived 2026-07-29 lowercase migration
      (`tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md`) is the direction to reverse. This supersedes the
      2026-08-03 slot-7 "interim guidance, not a final human sign-off" note below with a genuine operator answer.
      Approved raising the script's STOP-ON-SURPRISE ceiling and re-running `--apply` against the now-understood
      ~1.4M-row population — the seeding-function precondition (`-002`) was already satisfied before this ruling landed
      (`instruments-service@47a631ff` + `d79b9d74`).
- [x] ✅ [DATA] P1. Verify whether
      `instruments-service/scripts/enumerate_expected_universe.py::_canonical_writer_instrument_type` still seeds
      `expected_unattempted` rows in lowercase while MTDS's writer now captures in UPPERCASE (post
      `unified-trading-library@688e49bc`) — if confirmed, fix the seeding function to match the ruled-canonical casing
      so seed/capture shard atoms stay aligned. (repo: instruments-service) — DONE `instruments-service@47a631ff`.
      CONFIRMED the mismatch was real and live: the manifest consolidator's dedup key
      (`unified_trading_library.manifest_consolidator._dedup_key_sql`) has NO `UPPER()`/`LOWER()` normalization —
      case-sensitive — so a lowercase-seeded `combo`/`equity`/`etf`/etc. cell could never be superseded by its real
      (now-uppercase) capture. Fixed by routing `_canonical_writer_instrument_type`'s final grain through
      `canonicalize_manifest_instrument_type` (the SAME function the writer calls at the ManifestWriter seam) instead of
      re-hardcoding a casing assumption a second time — `futures_chain`/`options_chain` correctly stay lowercase
      (permanent bundle-grain exclusion), every other type (incl. `combo`) now matches the writer's actual UPPERCASE
      output. Updated 4 existing tests whose `present_set` fixtures hardcoded the stale lowercase grain; added a
      regression test asserting the seeder can never re-diverge from the writer's canon. Full QG green (5195 tests,
      `.qg_last_passed_sha=47a631ff`).
- [x] ✅ [DATA] P1. Once the direction is ruled + the seeding function (if broken) is fixed: re-run
      `market-tick-data-service/scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` (raising
      `_EXPECTED_CANDIDATE_MIN`/`_EXPECTED_CANDIDATE_MAX` to bracket the now-understood ~1.4M-row population) if
      UPPERCASE is ruled, OR write the equivalent lowercase-direction script update if LOWERCASE is ruled instead.
      (repo: market-tick-data-service) — DONE `market-tick-data-service@4cae1cb0` (ceiling raise,
      `_EXPECTED_CANDIDATE_MAX` 500,000 → 2,000,000, full QG green) + the real `--apply`, run 2026-08-04. Fresh dry-run
      immediately before applying confirmed the population was stable (1,401,523 changed vs the diagnosis's 1,401,491
      the prior day — ~30 rows of ordinary organic growth, not runaway). First two `--apply` attempts hit the documented
      CAS-write race (the manifest consolidator writes roughly every minute; this script's read-mutate-write window was
      ~20-40s, close enough to collide twice in a row) — both aborted UNCHANGED-SAFE per the script's own CAS design, no
      partial write. Per the script's own module docstring, paused
      `uts-prod-manifest-consolidator-market-data-tradfi-cron` for the single write attempt, applied, then immediately
      resumed it (confirmed `state=ENABLED` again). **Result**: 6,600,032 rows rewritten in place (row count preserved),
      generation `1785833448588065` → `1785833526440245`, pre-migration snapshot at
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/backups/availability_index.pre_itype_casing_100pct_20260804T085152Z.parquet`,
      1,401,523 `instrument_type` values case-corrected to UPPERCASE. Script's own self-verify: 5,860,660/5,860,660
      canonical. **Independently re-verified with a genuinely fresh read** (not the script's in-memory frame, per this
      repo's own established convention) against the confirmed post-apply generation: 5,860,660/5,860,660 canonical, 0
      residual. The tradfi manifest `instrument_type` column is now literal-100% UPPERCASE (excluding the permanent
      `futures_chain`/`options_chain` bundle-grain exclusion).
- [x] ✅ [DATA] P2. Cross-reference this doc, `tradfi_casing_100pct_redrift_2026_07_27.md`, and the archived
      `tradfi_combo_uppercase_casing_manifest_residual_2026_07_28.md` from each other so future casing work sees all
      three. (repo: unified-trading-pm) — DONE. This doc already cited both in its own `related:` at filing time; added
      the reciprocal `related:` pointer + a dated Progress Log note to the archived residual doc, and a `related:`
      pointer to the archived 100pct-directive doc, both pointing back at this doc.

## Progress Log

- 2026-08-03 (slot-7): filed after `tradfi_casing_100pct_redrift-014`'s dry-run surfaced the 17x population surprise;
  root-caused to the archived 07-28/29 lowercase migration via GCS backup-snapshot filenames
  (`_index/backups/availability_index.pre_combo_casing_relabel_2026072*`) cross-referenced to the archived issue's
  Progress Log. No code changed, no manifest write attempted.
- 2026-08-03 (slot-8): worked `-003` (re-run the migration). Confirmed via `/boot` that this todo is itself gated by
  `-001` ([OPERATOR] direction ruling — status=blocked, awaiting answer) and `-002` (seeding-function fix — status=
  dispatched to another slot); the backlog dispatcher offered `-002` and `-003` concurrently while `-001` was still
  open, which is the exact out-of-order dispatch this doc's own "Once the direction is ruled..." phrasing was meant to
  prevent. Filed `BLK-17ef2351` rather than force `--apply` a third time. Added `sequential: true` to this doc's
  frontmatter so the dispatcher stops offering `-002`/`-003`/`-004` while an earlier todo in the chain is unresolved.
  Also read-confirmed (no code changed) the `-002` suspicion:
  `instruments-service/scripts/ enumerate_expected_universe.py::_canonical_writer_instrument_type` (line 1754) still
  returns `(instr.instrument_type or "").strip().lower()` for passthrough leaves, and the combo bundle leaf resolves to
  lowercase `combo` via `bundle_instrument_type_for_leaf` — both predate the UTL seam
  (`unified-trading-library@688e49bc`) that now canonicalizes the WRITER to UPPERCASE, so the seeding function is
  confirmed stale relative to current writer behavior (docstring at line 1719-1738 still documents the pre-seam
  lowercase writer convention). This is evidence for whoever works `-002`, not a fix — the correct target casing for the
  seed still depends on `-001`'s ruling. No manifest write attempted; no `--apply` run.
- 2026-08-03 (slot-7): main gave interim guidance on the blocked question filed for `-001` (NOT a final human sign-off —
  a genuinely open P0 gate still awaiting the actual operator; deliberately NOT citing the tracking id in this note —
  see `/plans/archive/issues/blocked_reconcile_marker_false_positive_2026_08_03.md`, filed by a sibling slot the same
  day, for exactly why — since fixed and archived, `agent-orchestrator@209cd00`). Guidance splits into two parts: the
  likely-correct CASING DIRECTION (uppercase, IF this doc's premises hold — UAC's `InstrumentType.COMBO` enum value +
  the existing operator directive already on file in `tradfi_casing_100pct_redrift_2026_07_27.md`) still needs genuine
  operator confirmation, not just chat-level agreement; the `--apply` EXECUTION itself is explicitly withheld this tick
  — human-owned, given it's a THIRD mass rewrite of a contested ~1.4M-row population, requires loosening the script's
  own STOP-ON-SURPRISE safety guard, and has no verifiable before/after evidence artifact for a mutation this size (see
  `archive/2026_08/issues/prod_mutation_evidence_artifact_gap_2026_08_03.md`, archived 2026-08-13). One hard,
  non-negotiable prerequisite applies regardless of who ultimately signs off: fix the seeding-function staleness FIRST.
  Acted on that — closed `-002` for real this time (`instruments-service@47a631ff`, full QG green, see `-002` above) and
  closed `-004` (cross-reference). `-001` (the casing-direction decision) and `-003` (the `--apply` itself) stay OPEN,
  still gated on the human operator — no manifest write attempted this session.
- 2026-08-03 (slot-11): dispatched `-002` independently (concurrently with slot-7, before their `47a631ff` landed on
  origin), then found on rebase that slot-7 had already shipped the same seeder-side fix. Reconciling, found `47a631ff`
  left a SECOND, still-live half of the same bug: `_rollup_present_bundle_grain` (the present-set/`_build_present_set`
  side, used to convert a raw manifest read into the row-key set the seeder diffs against) re-keys a LEAF-shaped
  captured `combo` row to the writer's bundle grain via `bundle_instrument_type_for_leaf`, whose static map value is
  ALWAYS lowercase — untouched by `47a631ff`, which only fixed the seed side (`_canonical_writer_instrument_type`).
  Confirmed live (before my fix): a real captured `combo` row, once rolled up through `_build_present_set`, was forced
  back to lowercase `combo` while the seed now emits uppercase `COMBO` — the exact shard-atom mismatch `47a631ff` closed
  on the seed side, reopened immediately on the present-set side (any real captured combo cell — leaf-shaped or already
  bundle-shaped, `is_leaf` is keyed on `instrument_type` alone, not on whether `instrument_id` is blank — would never
  suppress its own seed). Verified via before/after: reverting just the present-set-side hunk makes
  `test_build_present_set_rolls_up_leaf_combo_capture_to_bundle_grain` and
  `test_enumerate_v2_tradfi_leaf_shaped_combo_capture_suppresses_phantom_seed` fail with `('COMBO', '', 'ES')` still
  present in the seeded output. Fixed by routing `_rollup_present_bundle_grain`'s `bundle_it_by_key` through the SAME
  `canonicalize_manifest_instrument_type` call (no-op for `futures_chain`/`options_chain`, the permanent bundle-grain
  exclusion) — `instruments-service@d79b9d74`, full QG green (5195 tests, `.qg_last_passed_sha=d79b9d74`), verified on
  origin. Todo `-002`'s checkbox was already flipped by slot-7; this entry documents the follow-up fix landed on top of
  it under the same todo (no separate checkbox — the todo's own outcome wasn't actually fully closed until this commit).
  `-001` (casing-direction) and `-003` (`--apply`) remain OPEN, still gated on the human operator — no manifest write
  attempted this session.
- **context-scout 2026-08-03**: populated context_scope (6 entries) — the two contradictory "resolved" migration threads
  this doc reconciles, the UAC enum that's the actual schema SSOT, the seeding function flagged as possibly-stale, the
  UTL canon function the casing-direction fix hinges on, and the script todo 3 would re-run.
- **context-scout 2026-08-03** (second pass, refreshed methodology): re-verified, unchanged (6 entries) — the
  `enumerate_expected_universe.py` entry already listed is confirmed to be the exact file the
  `_rollup_present_bundle_grain` fix landed in this session; `-001`/`-003` remain gated on the same operator decision.
- **slot-7 2026-08-03 (pre-compact checkpoint)**: extended idle wait on `-001` — confirmed via repeated `/api/backlog`
  polls it stayed `status: blocked` throughout, no operator ruling landed. Checkpoint audit: all four touched repos
  (instruments-service, unified-trading-pm, unified-trading-library read-only, market-tick-data-service read-only)
  clean, `ahead=0` against `origin/live-defi-rollout`; scratchpad empty (the one diagnostic script used mid-session was
  deleted after its findings were folded into this doc's "What I found" section — nothing left pointing at it); no
  chat-only findings outstanding — every discovery this session (prereq verification, the 17x population surprise, the
  root-cause, the SSOT contradiction, the seeder fix, slot-11's present-set-rollup follow-up) already lives in a
  committed+pushed doc or commit, not just this Progress Log. Nothing at risk from a compact/session-end here. `-001`
  (casing direction) and `-003` (the `--apply`) remain the only open items, both genuinely operator-owned — next session
  should resume by polling `/api/backlog` for `-001`'s status before doing anything else.
- **2026-08-04 (interactive session, operator direct)**: `-001` RULED — **UPPERCASE**, per the recommended-decision
  section above (UAC schema enum + existing operator precedent). This is the genuine operator answer the 2026-08-03
  slot-7 entry above was still waiting on. Todo `-003` (the actual `--apply` re-run, raising the script's
  STOP-ON-SURPRISE ceiling to bracket the ~1.4M-row population) is now unblocked but was NOT executed this session — it
  is a third mass rewrite of a contested, already-twice-flipped production population, requires loosening a safety
  guard, and per this doc's own 2026-08-03 slot-7 note has no verifiable before/after evidence artifact yet
  (`archive/2026_08/issues/prod_mutation_evidence_artifact_gap_2026_08_03.md`, archived 2026-08-13 — the evidence-
  artifact convention it asked for now exists via PLAN_FORMAT.md § 8d). Left for a dedicated execution pass
  (VM/orchestrator dispatch, since this doc is `assigned_vm: planning`) rather than run ad hoc from an interactive
  session.
