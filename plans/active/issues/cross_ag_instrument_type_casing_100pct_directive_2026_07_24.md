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
status: open
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
resolved_by:
drift_direction: advance-code
depends_on: []
---

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
- [ ] [DATA] P2. When any of `cefi_consolidated_closeout_2026_07_18.md` / `defi_consolidated_closeout_2026_07_18.md` /
      `tradfi_manifest_content_recovery_completion_2026_07_24.md` is next split under
      `plan_line_cap_remediation_2026_07_23.md`, fold this doc's cefi/defi/tradfi-specific "target = 100%" /
      "DeFi-specific refinement" language into the relevant child plan directly (verbatim, per the split convention used
      elsewhere this session) rather than leaving it only cross-referenced here.
