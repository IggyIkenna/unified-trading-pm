---
doc_type: issue
title:
  "OPERATOR DECISION: DeFi POOL rows — the backfill script's docstring and the catalogue roll-up's pinned test assert
  OPPOSITE policies for `canonical_instrument_id`. Both cannot be true; the roll-up currently honours the test."
summary:
  "Found 2026-07-17 (slot-3) while fixing the CeFi Phase -1 catalogue verify gate (canonical-completeness program).
  `scripts/backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`'s docstring states the invariant `instrument_id ==
  canonical_instrument_id` holds for DeFi rows **'pool or not'**. But
  `tests/unit/scripts/test_build_instrument_catalogue.py::test_rollup_defi_pool_row_backfills_canonical_instrument_id_from_instrument_key`
  pins the OPPOSITE for POOL rows — `instrument_id` = pool_address while `canonical_instrument_id` = the glued key — and
  its comment attributes that to an 'operator-approved policy'. The two are in direct contradiction. This does NOT
  affect the CeFi gate (no POOL rows in cefi) and did not block the cefi fix (`instruments-service@517b817b`), which
  deliberately canonicalized the mirror SOURCE rather than blanket-copying the emitted id specifically to preserve the
  POOL contract the test pins. Filed per the findings-triage HARD RULE (SSOT contradiction = NOTIFY OPERATOR + issue
  doc). Needs a DeFi ruling on which policy is authoritative, then reconcile the losing side."
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [defi, canonical-instrument-id, pool, ssot-contradiction, catalogue, instruments-service]
related:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "Discovered by the Phase -1 catalogue-defect fix (slot-3, 2026-07-17) for the CeFi canonical-completeness program;
  surfaced while deciding whether `canonical_instrument_id` could be blanket-mirrored onto the rebuilt `instrument_id`."
resolved_by: instruments-service@c31d37c3, unified-api-contracts@e319864f
---

# DeFi POOL rows: `canonical_instrument_id` policy contradiction

## The contradiction (both cannot be true)

| Source                                                                                                                                                       | Asserts                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments-service/scripts/backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py` (docstring)                                                          | `instrument_id == canonical_instrument_id` holds for DeFi rows — explicitly **"pool or not"**                                                                 |
| `instruments-service/tests/unit/scripts/test_build_instrument_catalogue.py::test_rollup_defi_pool_row_backfills_canonical_instrument_id_from_instrument_key` | For **POOL** rows they DIVERGE: `instrument_id` = `pool_address`, `canonical_instrument_id` = the glued key — comment cites an **"operator-approved policy"** |

The catalogue roll-up (`scripts/build_instrument_catalogue.py`) currently honours the **test** (divergence for POOL
rows). So today's live DeFi POOL rows carry `instrument_id != canonical_instrument_id` **by design**, which directly
falsifies the backfill script's stated invariant.

## Why it surfaced now (and why it did NOT block the CeFi work)

The CeFi Phase -1 verify gate requires `instrument_id == canonical_instrument_id` for **cefi** rows (511 cefi FUTURE
rows were drifting because `instruments-service@79d4dbcb` rebuilt `instrument_id` but left the mirror sourcing the stale
value). The obvious fix — blanket-copy the emitted `instrument_id` into `canonical_instrument_id` — would have
**silently broken the DeFi POOL contract** the test pins. Instead `instruments-service@517b817b` canonicalizes the
mirror **source** through a shared `_canonicalize_cefi_rollup_id()` chain, leaving the POOL divergence intact. So the
cefi gate closes without ruling on DeFi. **No cefi rows are POOL rows** — the contradiction is DeFi-only.

## Why it matters

- `canonical_instrument_id` is **live-consumed**, not vestigial — `scripts/enumerate_expected_universe.py`,
  `scripts/backfill_spot_asset_population_2026_07_16.py:324` (which itself writes
  `canonical_instrument_id := instrument_id`),
  `scripts/canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py`,
  `scripts/reclassify_defi_postdelist_eu_2026_06_24.py`, and MTDS `scripts/migrate_onchain_perp_*`. A consumer that
  trusts the backfill script's "pool or not" invariant will mis-key every DeFi POOL row.
- Two scripts writing under opposite invariants against the same column is a latent corruption source: whichever runs
  last wins, silently.

## Options (operator ruling needed — DeFi scope)

- **A [REC] — the TEST is authoritative; fix the docstring.** POOL rows legitimately diverge (`instrument_id` =
  pool_address is the addressable identity; `canonical_instrument_id` = the glued key is the human/canonical identity).
  Correct `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`'s docstring to carve POOL out, and audit its code
  path for whether it actually enforces the wrong invariant on POOL rows (docstring-only vs real behaviour — NOT yet
  verified, see below).
- **B — the DOCSTRING is authoritative; POOL rows must converge.** Then the pinned test + the roll-up's
  `_defi_pool_dual_form` branch are wrong and DeFi POOL identity changes corpus-wide (large blast radius: every DeFi
  POOL manifest key + enumerator row).
- **Other** — a third policy (e.g. keep divergence but rename the column so the intent is unambiguous).

## Open / not verified

- **Whether the backfill script's CODE actually violates the POOL contract, or only its docstring does.** Only the
  docstring was read (during a cefi-scoped fix); its DeFi POOL code path was not traced. Diagnose both sides before
  editing (findings-triage) — if the code already carves POOL out, this collapses to a one-line docstring fix (option A,
  trivial).
- Live measurement of how many DeFi POOL rows currently diverge, and whether any consumer is already mis-keying them.

## Todos

- [x] [BACKEND] P2. Trace `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`'s POOL code path — does it enforce
      the docstring's "pool or not" invariant, or does it already carve POOL out (making this a docstring-only defect)?
      (repo: instruments-service) — instruments-service@c31d37c3.
- [x] [BACKEND] P2. Apply the operator's ruling (default **A** if none given: test wins, fix the docstring), reconcile
      the losing side, and add a single pinned test naming the authoritative policy so this cannot re-diverge. (repo:
      instruments-service) — instruments-service@c31d37c3, unified-api-contracts@e319864f.

## RESOLVED (2026-07-25)

Frontmatter flipped per the defi orphan-audit (2026-07-25). Both todos above closed by
`defi_track01_per_instrument_and_canon_id_2026_07_24.md` (extracted verbatim from
`defi_consolidated_closeout_2026_07_18.md`'s own Track 1 — CANON section for line-cap reasons), which cites this issue
doc by filename: "✅ SHIPPED (Option A pinned) instruments-service@c31d37c3 + unified-api-contracts@e319864f. Backfill
docstring POOL carve-out corrected + CODE-path-doesn't-converge-POOL verified + pinning test
test_pool_rows_diverge_option_a_and_backfill_does_not_enforce_convergence."
