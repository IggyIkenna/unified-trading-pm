---
doc_type: issue
title:
  "Cross-AG instrument_type manifest casing — 4 of 5 asset_groups target literal 100% UPPERCASE, DeFi is the sole
  per-instrument_type exception"
summary: >-
  Operator directive (2026-07-24), sharpening operator ruling D1 (2026-07-20,
  `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1: manifest `instrument_type` COLUMN canonical target is
  UPPERCASE). D1 measured tradfi/cefi/prediction as already near-uniform (tradfi 3.3M UPPERCASE re-stamps applied; cefi
  ~99.41% UPPER; prediction 99.46% UPPER) and DeFi as genuinely mixed ("both cases present"). Operator ruling this
  session: tradfi, cefi, prediction, and sports all target literal 100% (not "substantially complete" / the historical
  ~99% snapshots) — finish them, don't stop short, so the deployment-ui data-status Distinct Values panel shows 0
  non-canonical `instrument_type` entries for each. **DeFi is the sole exception**: because its corpus is genuinely
  mixed rather than close-to-one-direction, blanket UPPERCASE is not necessarily the cheap/correct direction there —
  canonical casing for DeFi is decided PER `instrument_type` value on a least-migration-cost basis (whichever casing is
  already dominant for that value becomes its target; the minority migrates to match). Hard constraint, cross-AG: within
  one `(instrument_type, asset_group)` pair the casing MUST be 100% consistent — accepting both cases for the same pair
  is never acceptable. Different `instrument_type` values ARE allowed to land on different canonical casings from EACH
  OTHER within DeFi only. The GCS path-segment (always lowercase) and id-middle-segment (always UPPER) legs are
  unchanged by any of this — only the manifest COLUMN casing target is affected.
status: resolved # (was: open) 2026-08-02 -- all 3 todos done, doc archived per the 6-step ritual
nature: issue
asset_group: [tradfi, cefi, defi, prediction, sports]
stage: [data]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-ui,
  ]
scope: [engineer]
tags: [data-correctness, instrument-type, casing, canonical-id, cross-asset-group, operator-directive, data-status]
related:
  [
    tradfi_manifest_content_recovery_completion_2026_07_24,
    cefi_consolidated_closeout_2026_07_18,
    defi_consolidated_closeout_2026_07_18,
    defi_track01_per_instrument_and_canon_id_2026_07_24,
    prediction_phase_ab_residuals_2026_07_24,
    sports_consolidated_closeout_2026_07_19,
  ]
created: 2026-07-24
parent_epic: infrastructure_master
priority: P1
source:
  "Operator, 2026-07-24, in direct follow-up to the D1 ruling recap given this session — asked whether the workspace
  should treat instrument_type casing uniformly (some things ARE canonical lowercase across AGs — data_types; venues and
  chains are always uppercase; instrument_type is mixed in both manifest and path names today) and directed a
  path-of-least-resistance policy: whichever casing requires the least manifest/path migration wins PER
  (instrument_type, asset_group) combination, with the hard constraint that a single combination must never accept both
  cases. On learning D1 already measured tradfi/cefi/prediction as near-uniform-UPPERCASE and only DeFi as genuinely
  mixed, the operator ruled: the other 4 AGs just finish to literal 100% (that IS the least-resistance direction for
  them), DeFi alone gets the per-instrument_type treatment. Then directed this be written into all 5 AG consolidated
  plans; created as a standalone issue doc (this file) rather than duplicated inline in
  cefi_consolidated_closeout_2026_07_18.md / defi_consolidated_closeout_2026_07_18.md /
  tradfi_manifest_content_recovery_completion_2026_07_24.md because those 3 files are already over the plans/active/*.md
  1000-line hard cap (pre-existing, tracked debt — see plans/active/issues/plan_line_cap_remediation_2026_07_23.md;
  hard_count=17 in scripts/plan-hygiene/line_caps_baseline.yaml as of today) and the RULE-11 blast-radius line-cap gate
  blocks ANY staged touch to an over-cap file, not just growth — touching them to add even a few lines is blocked until
  they are split, which is out of scope for this directive."
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by: slot-8, cross_ag_instrument_type_casing_100pct_directive-002, 2026-08-02
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
  ]
---

> **✅ ARCHIVED 2026-08-02 — all 3 todos done, all per-AG execution items closed or pointed at their live homes.**
> Codex-alignment check: **no new codex content required.** All 3 correction-banner sections this doc's own P1 todo
> added (`/codex/02-data/canonical-cutover-register.md` §3c/§7, `/codex/02-data/cross-asset-canonical-target-ssot.md`
> §7, `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1) already restate the full operator-directive framing
> verbatim, not a bare citation — updated their path pointers to this archive location only. The D1 measurement snapshot
> figures (tradfi 3,300,155 re-stamps; cefi ~99.41%; prediction 99.46%) are independently already recorded in
> `reconciliation-finding-taxonomy.md` §5.1; sports' distinct content-bug detail already lives in
> `/plans/active/sports_consolidated_closeout_2026_07_19.md` (execution-appropriate, not a codex-durable contract). 15
> of the 16 corpus-wide referrers found via
> `grep -rl cross_ag_instrument_type_casing_100pct_directive_2026_07_24 --include=*.md .` had their path updated to this
> archive location in the same session; the 16th
> (`/plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:445`) is a bare-slug mention inside a
> past-tense retrospective sentence with no path/extension to fix — left as historical narrative, unchanged. See the
> doc's own "Where each asset_group's execution item lives" section below for the live per-AG work (tradfi/defi
> resolved; cefi/prediction/sports still have open execution items in their own plans, unaffected by this archival —
> this doc's own scope was the CROSS-AG DIRECTIVE, not the per-AG execution, which was always tracked in those other
> plans).

# Cross-AG instrument_type manifest casing — 100% target for 4 AGs, per-value least-resistance for DeFi

## The standing D1 ruling (context, not re-litigated here)

`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1, operator ruling D1 (2026-07-20): the canonical TARGET for the
manifest `instrument_type` COLUMN is **UPPERCASE** (the catalogue enum:
`{FUTURE, OPTION, EQUITY, ETF, INDEX, COMBO, SPOT_PAIR}`). Two things are separately, permanently ruled and **never in
question** regardless of anything in this doc: the **GCS path segment** stays lowercase, and the **id middle segment**
stays UPPER. Only the manifest COLUMN's casing was ever open, and D1 settled it — this doc sharpens _how far_ each
asset_group must go, not the direction itself.

D1's own measurement, at ruling time (2026-07-20):

| Asset group | Measured state (2026-07-20)                                                            | Direction           |
| ----------- | -------------------------------------------------------------------------------------- | ------------------- |
| prediction  | 99.46% UPPER                                                                           | near-uniform        |
| cefi        | ~99.41% UPPER (adjusted)                                                               | near-uniform        |
| tradfi      | 3,300,155 UPPERCASE re-stamps already applied                                          | already migrated    |
| defi        | "both cases present"                                                                   | **genuinely mixed** |
| sports      | not in the D1 snapshot (sports has its own, different instrument_type bug — see below) | —                   |

## Operator directive (2026-07-24)

**For tradfi, cefi, prediction, sports: target is literal 100%, not the historical ~99% snapshots or "substantially
complete."** These four are already close-to-uniform-UPPERCASE (or, for sports, resolve through an already-UPPER target
vocabulary once a separate content bug is fixed — see below), so finishing to 100% genuinely IS the least-migration-cost
direction for each of them. Do not stop at "mostly done" — the deployment-ui data-status Distinct Values panel must show
**0 non-canonical `instrument_type` entries** for each of these four asset_groups.

**For DeFi alone: casing is decided PER `instrument_type` value, on a least-migration-cost basis.** DeFi's corpus was
separately flagged in the SAME D1 measurement as genuinely mixed, not close-to-one-direction — a blanket push to
UPPERCASE is not necessarily the cheap direction here the way it is for the other four. Decision: for each DeFi
`instrument_type` value (`POOL`, `LENDING`, `PERPETUAL`, `YIELD_BEARING`, `STAKING`, `SPOT_PAIR`, …), whichever casing
is ALREADY dominant becomes that value's canonical target, and the minority migrates to match.

**Hard constraint, cross-AG, non-negotiable**: within one `(instrument_type, asset_group)` pair, casing MUST be 100%
consistent. Accepting both upper and lower for the SAME pair is never an option, in any asset_group. Different
`instrument_type` values ARE allowed to land on different canonical casings from EACH OTHER — this per-value freedom is
DeFi-only; the other four asset_groups' per-value target is uniformly UPPERCASE.

## Where each asset_group's execution item lives

- **tradfi**: ✅ **RESOLVED 2026-07-25** — `plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`, the
  "Converge every WRITER's `instrument_type` emission to the UPPERCASE enum" + "Enumeration-driven migration" P0 todos.
  Writer fix (`market-tick-data-service@020b703e`) + migration (`@4e631a3d`, applied live: 45,681 case-corrected). Fresh
  live re-read this session (post-apply): `Rows CHANGED: 0`, self-verify `4,988,822/4,988,822 UPPERCASE` — 0
  non-canonical `instrument_type` rows remain for tradfi. Full evidence in the child plan.
- **cefi**: `plans/active/cefi_consolidated_closeout_2026_07_18.md`, the "instrument_type column normalization" todo
  (P0, script built + dry-run validated at 99.41%/97.49%, `--apply` DRAIN-GATED under the Track-1 cutover). Running the
  cutover `--apply` is necessary but the item does not close on `--apply` alone — done when a fresh live read
  post-cutover shows 0 non-canonical rows and the data-status panel agrees.
- **prediction**: `plans/active/prediction_phase_ab_residuals_2026_07_24.md` — a new P0 todo added 2026-07-24
  reconciling two disagreeing historical numbers (tick-18's `--apply` measured 11.80%→100% on 2026-07-19; the D1
  snapshot measured only 99.46% one day later, most likely because ongoing captures between the two reads re-introduced
  non-canonical rows before the tick-21 durability fix landed). Done when a FRESH live read shows literal 0
  non-canonical rows, not either historical snapshot.
- **sports**: `plans/active/sports_consolidated_closeout_2026_07_19.md`, Track C's existing "0 non-canonical across all
  four axes" target (venues/instrument_types/data_types/chains) — this is a distinct, deeper content bug (the writer
  reads the wrong colon-delimited segment of the canonical id, producing bookmaker names as `instrument_type` values,
  not a pure casing drift), but its target vocabulary (`ODDS_API_MARKET_TO_CANONICAL`) is already UPPER on `market_key`,
  so fixing the content bug lands on the same 100%-UPPERCASE casing target as the other three without a separate casing
  migration.
- **defi**: ✅ **RESOLVED 2026-07-24** (autonomous session) —
  `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`, the "Manifest instrument_type case +
  venue-spelling unify" todo. The required census ran live: all 11 distinct `instrument_type` values are already 100%
  one casing (lowercase, 0 exceptions) — least-migration-cost target = each value's already-unanimous casing, no
  migration needed. Venue-spelling half also closed as a no-op for a different reason: 3 of 5 named pairs are already
  zero-residual, and the other 2 (`AAVE`, `MORPHOVAULTS`) turned out to be genuinely distinct, deliberately-registered
  venues (not spelling drift) per a 2026-07-21 UAC registration this todo's source audits predate — collapsing them
  would have been a regression. Full evidence in the child plan.

## Why this is a standalone issue doc, not inline in 3 of the plans

`cefi_consolidated_closeout_2026_07_18.md` (1421L), `defi_consolidated_closeout_2026_07_18.md` (1489L), and
`tradfi_manifest_content_recovery_completion_2026_07_24.md` (1633L) are all already over the `plans/active/*.md`
1000-line hard cap — pre-existing, tracked debt (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`,
`hard_count: 17` in `scripts/plan-hygiene/line_caps_baseline.yaml`). The `check_line_caps.sh` pre-commit gate is a
RULE-11 blast-radius safety check: **a file THIS commit touches must not be over its tier's cap, full stop** — it blocks
staging ANY change to an already-over-cap file, not just growth. Splitting these 3 files is real, separate work (the
same pattern already applied to `tradfi_consolidated_closeout_2026_07_18.md`,
`prediction_consolidated_closeout_2026_07_18.md`, and `defi_consolidated_closeout_2026_07_18.md`'s own Track-1
extraction) and is out of scope for this directive — it belongs to the tracked remediation issue, not this one. This doc
is the durable record; the 5 per-AG plans' execution-item pointers above are how to find the live work.

## Open todo

- [x] ✅ [DOC] P1. **DONE 2026-07-24 (autonomous session).** Found + corrected a stale-SSOT chain this directive left
      behind: `reconciliation-finding-taxonomy.md` §5.1 carried an EARLIER-same-day "scope correction" (commit
      `4f81d0139`, 19:11:01 UTC — an agent's inference from `_comparison_set()`'s case-insensitive vocabulary-matching
      grain rule) declaring defi permanently lowercase and OUT of any casing-migration population; this directive's own
      commit (`adb28421d`, 19:31:37 UTC — ~20 min later) already superseded that by putting defi back in scope for the
      per-value least-migration-cost convergence, but no doc ever recorded the supersession, and
      `canonical-cutover-register.md` §3c/§7 + `cross-asset-canonical-target-ssot.md` §7 still separately carried the
      ORIGINAL (2026-07-20) blanket-UPPER-for-defi-too framing, predating both corrections. Added dated correction
      banners to all three codex docs pointing at this directive as authoritative, without deleting the superseded text
      (matches the existing struck-through-banner convention). No operator input needed — resolved by commit timestamp +
      the fact that one side is an explicit fresh operator statement and the other an agent's inference from unrelated
      code.
- [x] ✅ [DATA] P2. **DONE 2026-08-02 (data_engineering slot-7).** The trigger condition already fired:
      `plan_line_cap_remediation_2026_07_23.md` (`status: resolved`, now archived) already split all 3 named files below
      the 1000-line cap (cefi 1421L→561L, defi 1489L→914L, tradfi 1633L→1000L) before this todo was ever dispatched.
      Checked each for the fold-in: **tradfi** already cited this directive by name (line 263, done 2026-07-25 as part
      of its own casing todo — no action needed). **cefi** did not cite this directive at all — its 2026-07-27
      enumeration-audit checkpoint left a 2,982-row `instrument_type` non-canonical residual undescribed against the
      literal-100% bar; added a new P2 todo citing this directive + the residual, done-when = a fresh live recount
      hits 0. **defi** carried STALE pre-2026-07-24 text (the blanket-manifest-COLUMN-UPPERCASE framing this directive's
      own DOC todo above already knew was superseded for DeFi specifically) with no mention of the 2026-07-24 per-value
      refinement or its 2026-07-24 resolution (`defi_track01_per_instrument_and_canon_id_2026_07_24.md`,
      already-100%-lowercase census, no migration needed) — corrected that section in place, citing both this directive
      and the resolving todo. No production data touched — pure documentation fold-in, per this todo's own scope.
- [x] ✅ [DOC] P3. **DONE 2026-08-02 (slot-8).** Codex-alignment check resolved FIRST (before the move): read all 3
      correction-banner sections in full (`canonical-cutover-register.md` §3c/§7, `cross-asset-canonical-target-ssot.md`
      §7, `reconciliation-finding-taxonomy.md` §5.1) — each already restates the full operator-directive framing
      verbatim (the per-value least-migration-cost rule + the hard cross-AG consistency constraint + the execution
      pointer), not a bare citation. The D1 measurement snapshot figures are independently already recorded in codex too
      (tradfi's 3,300,155 re-stamp count and the 99.46%/99.41% cefi/prediction figures both live in
      `reconciliation-finding-taxonomy.md` §5.1); the table's sports row is a "not measured by D1" absence-note, not a
      fact needing a codex home, and sports' own content-bug detail already lives in
      `sports_consolidated_closeout_2026_07_19.md` (execution-appropriate, not a codex-durable contract). Verdict: **no
      new codex content required** — updated the 3 banners' path pointers only (post-move path), same session as the
      other 12 non-codex corpus-wide referrer fixes (15 of 16 hits fixed total; the 16th,
      `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:445`, is a bare-slug mention inside a past-tense
      retrospective sentence with no path/extension to fix — left as historical narrative). Moved to
      `plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md` with an ARCHIVED banner;
      `status: resolved`, `resolved_by` filled in. No CLAUDE.md change needed — this closes an existing directive, it
      doesn't ship a new contract beyond what the 3 codex docs already carry. (repo: unified-trading-pm)

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries). Note:
  `plan_line_cap_remediation_2026_07_23.md` (cited above and in this doc's own P2 todo) has since moved to
  `/plans/archive/issues/` — the todo's gating condition may need re-verification against the archived doc's resolution
  state.
- **data_engineering slot-7, 2026-08-02**: confirmed the archived remediation doc's `status: resolved` and its split
  table show all 3 named plans already split (cefi/defi/tradfi all now well under the 1000-line cap) — the P2 fold-in
  todo's trigger condition had already fired. Did the fold-in (see the flipped todo above) directly rather than
  re-verifying the gate a second time.
