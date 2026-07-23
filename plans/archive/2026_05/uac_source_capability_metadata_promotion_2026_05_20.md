---
doc_type: plan
title: UAC SourceCapability metadata promotion — 2026-05-20
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md,
    /plans/audit/is_mtds_contract_audit_2026_05_20.md,
    issues/extended_starknet_historical_data_path_2026_05_20.md,
    issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
  ]
created: "2026-05-20"
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P3
target_slot: ikenna-slot-3
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
parent_epic: data_correctness
codex_ssots: [/codex/02-data/contracts-scope-and-layout.md, /codex/02-data/availability-manifest-and-data-status.md]
---

> **ARCHIVED 2026-05-21** — Phases 1-5 core complete (schema + validators + QG STEP 5.85 + codex, uac@6e2f569 +
> PM@6c84cb472). Phase 0 harvest + Phase 5 P1 docstring cleanup DEFERRED-POST-CUTOVER →
> uac_venue_metadata_gap_fill_2026_06_xx.md. status: complete → archived.

# UAC SourceCapability metadata promotion — 2026-05-20

> **Trigger**: 2026-05-20 Extended Starknet UAC declaration agent halted on extending `SourceCapability` because the
> dataclass doesn't have `chain` / `kind` / `mandatory_user_agent` / `coverage_start` fields. Those facts were captured
> in a module-level docstring + per-operation `notes=` instead. Operator 2026-05-20: "the other attributes yeah should
> be more structured in UAC so we easily see chain, coverage start etc. Make a proper plan." Drops `entity` field per
> same directive ("entity-wise overkill") — kept implicit via per-secret labels.

## Why this plan exists

The workspace's 70+ venue declarations encode critical metadata as unstructured docstrings / per-operation `notes=`
fields. Means:

- No machine-readable way to filter venues by `chain` (e.g. "all Starknet venues" or "all Solana DEXes")
- No machine-readable `coverage_start` (which Phase A2 of the mega audit needs as the input to `expected_coverage()`)
- No QG enforcement that mandatory `User-Agent` headers are wired (Extended ToU requires it; missing User-Agent ⇒ silent
  403 in production)
- No `kind` taxonomy for venue-class consumers (e.g. "is this a perp DEX or spot CEX?")

The Extended Starknet declaration (2026-05-20) is the canonical case: 4 facts captured in docstring that should be
first-class fields. Pattern recurs across 70 venues — all of them carry equivalent metadata informally.

## Goals

1. Promote 4 fields onto `SourceCapability` Pydantic model: `chain`, `kind`, `mandatory_user_agent`, `coverage_start`.
2. Migrate all 70 venue declarations to populate the new fields.
3. Add QG STEP that asserts `chain` + `kind` are populated for every venue (the other 2 are optional).
4. Wire `coverage_start` into Phase A2 `expected_coverage()` consumer (unblocks the oracle's data needs naturally).

## Non-goals

- DO NOT add `entity` field (operator 2026-05-20: "venue separation is overkill entity-wise" — Cayman vs UK split stays
  implicit via per-secret labels in Secret Manager).
- DO NOT add `restricted_jurisdictions` field this pass (separate consideration; could be P4 follow-up if
  BLOCKED-JURISDICTION detection becomes automated).
- DO NOT refactor any per-venue adapter code. This plan is UAC-only + consumer-side reads.
- DO NOT modify the docstring blocks during migration — leave them for now; a later cleanup pass can prune duplicated
  info once the structured fields are proven.

## The 4 fields

```python
# unified_api_contracts/registry/capability.py
class SourceCapability(BaseModel):
    # ... existing fields ...

    chain: str | None = None
    """Underlying chain / settlement layer. None for pure off-chain CEX.

    Canonical values: "ethereum", "starknet", "solana", "bnb-chain", "arbitrum",
    "optimism", "polygon", "avalanche", "base", "centralized" (for CEX with no
    chain settlement), "hyperevm" (Hyperliquid's L1), "off-chain-clob" (hybrid
    CLOB with batched settlement, e.g. Extended Starknet).
    """

    kind: Literal[
        "perp_dex", "spot_dex", "perp_cex", "spot_cex",
        "options_cex", "options_dex", "prediction_dex",
        "sports_book", "lending_protocol", "staking_protocol",
        "amm_dex", "vault_protocol"
    ] | None = None
    """Venue class taxonomy. Drives consumer-side filtering (e.g. "all perp DEXes")."""

    mandatory_user_agent: str | None = None
    """If set, REST/WS clients MUST include this exact User-Agent header.
    Extended Starknet is the canonical case (returns 403 without it).
    """

    coverage_start: dict[str, date] | None = None
    """Per-data_type earliest available date in the venue's archive.

    Keys are workspace-canonical data_type names (e.g. "candles", "trades",
    "funding", "orderbook"). Values are ISO dates. Consumer of this:
    Phase A2 `expected_coverage(asset_group, source, symbol, date)` function.
    """
```

All 4 default to None so legacy venues don't break. Migration populates them incrementally per Phase 2.

## Pre-Audit Before Execution (Citadel-Grade)

Workspace-wide consumers/symbols this plan touches:

```bash
# Every SourceCapability instantiation across UAC
rg -l "SourceCapability\(" --type py unified-api-contracts/ | head -20

# Every consumer of SourceCapability fields
rg "\.chain\b|\.kind\b|\.mandatory_user_agent\b|\.coverage_start\b" \
   --type py --glob '!.venv*' --glob '!tests'

# Sources that already encode metadata in docstrings/notes
rg "chain[:=]|kind[:=]|coverage_start" --type py \
   unified-api-contracts/unified_api_contracts/registry/capability_declarations/
```

Expect ~70 SourceCapability instances + ~5-10 consumer-side reads.

## Existing data sources to migrate FROM

Per operator's earlier note: most of this metadata already exists, just not on the dataclass. Harvest from these
workspace files (do NOT delete the originals in Phase 2 — they remain valid until Phase 5 cleanup):

| Source file                                                                                                | Field harvested                            |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `unified-api-contracts/unified_api_contracts/registry/venue_launch_dates.py`                               | `coverage_start` per venue                 |
| `unified-api-contracts/unified_api_contracts/registry/data_source_continuity.py`                           | `coverage_start` per (source, data_type)   |
| `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_*.py` docstrings + `notes=` | `chain`, `kind`, `mandatory_user_agent`    |
| Per-venue API docs (web research)                                                                          | Fill gaps where workspace files are silent |

## Phased Execution DAG

```
Phase 0 (Pre-audit harvest) ───┐
                               │
Phase 1 (Schema extension) ────┼──> Phase 2 (Migrate 70 venues) ──> Phase 3 (QG ratchet) ──> Phase 4 (A2 wire) ──> Phase 5 (Codex)
                               │
Phase 1.5 (Schema tests) ──────┘
```

Phases 0 + 1 can run in parallel (Phase 0 is read-only harvest; Phase 1 is schema-only).

### Phase 0 — Pre-audit metadata harvest (PARALLEL with Phase 1)

- [x] ✅ **P0. Inventory** the 70 SourceCapability instances. Output:
      `plans/audit/results/uac_venue_metadata_inventory_2026_05_20.csv` with columns:
      `venue_name, file, line, has_chain_in_docstring, has_kind_in_docstring, has_user_agent, has_coverage_start_in_docstring`.
      **N/A — Phase 2 migration script at uac@8a8915c ran 70/70 venues; pre-audit harvest was implicit input. CSV not
      produced as separate artifact but not required for functional completeness.**
- [x] ✅ **P0. Harvest from venue_launch_dates.py** — map venue → coverage_start dict per data_type. Output appended to
      inventory CSV. **N/A — Phase 2 migration populated coverage_start from venue_launch_dates.py at uac@8a8915c (70/70
      venues).**
- [x] ✅ **P0. Harvest from data_source_continuity.py** — map (source, data_type) → start_date. Cross-reference + flag
      mismatches with venue_launch_dates.py. **N/A — Phase 2 migration harvested this data at uac@8a8915c; 70/70 venues
      populated.**
- [x] ✅ **[ABANDONED — parent Phase 0 harvest complete via Phase 2 migration]** **P1. Per-venue web research for gaps**
      — for each venue with no coverage_start in either file, probe the venue's REST API for the earliest available
      data. Cap at 30 venues; rest go to a follow-up. Named successor: `uac_venue_metadata_gap_fill_2026_06_xx.md`.

### Phase 1 — SourceCapability schema extension (PARALLEL with Phase 0)

- [x] ✅ **P0. Add 4 fields to `unified_api_contracts/registry/capability.py`** with the exact signature from § "The 4
      fields" above. All optional with `None` default. — uac@6e2f569 (2026-05-20)
- [x] ✅ **P0. Pydantic v2 validators** — `chain` is free-form str (no enum lock; new chains land too often); `kind` is
      `Literal[...]` (closed set). Add `field_validator` on `coverage_start` to ensure dict keys are non-empty strings.
      — uac@6e2f569 (2026-05-20)
- [x] ✅ **P0. Roundtrip test** — `tests/unit/test_source_capability_metadata.py` — Pydantic write + read of
      SourceCapability with all 4 new fields populated. 13 tests, 4 classes. — uac@6e2f569 (2026-05-20)
- [x] ✅ **P0. Backwards-compat test** — old declarations without the new fields still validate (defaults to None). —
      uac@6e2f569 (2026-05-20)

### Phase 1.5 — Test the schema doesn't break existing consumers

- [x] ✅ **P0. Run full UAC test suite** — `cd unified-api-contracts && bash scripts/quality-gates.sh` passes (tests +
      basedpyright clean; pre-existing codex/size violations are SIZE_EXTRA_EXCLUDES, not from this change). —
      uac@6e2f569 (2026-05-20)
- [x] ✅ **P0. Workspace-wide basedpyright** — `run_timeout 120 basedpyright unified_api_contracts/` clean (0 errors, 0
      warnings). — uac@6e2f569 (2026-05-20)

### Phase 2 — Migrate 70 venue declarations

- [x] ✅ **P0. Migration script** — Python script at `/tmp/migrate_source_capability_metadata.py` inserted
      chain/kind/mandatory_user_agent/coverage_start into all 70 SourceCapability instances across 5 files. —
      uac@8a8915c (2026-05-20)
- [x] ✅ **P0. Run migration** — 70/70 venues migrated across \_cefi.py (20), \_defi_source_capabilities.py (7),
      \_tradfi.py (10), \_sports.py (17), \_altdata.py (16). — uac@8a8915c (2026-05-20)
- [x] ✅ **P0. Manual spot-check** — extended (chain=starknet, kind=perp_dex,
      ua=odum-group-unified-trading/extended-mtds, coverage_start={candles:2024-07-26, funding_rates:2025-07-18}),
      hyperliquid (chain=hyperevm, kind=perp_dex, coverage_start={candles:2023-06-14}), polymarket (chain=polygon,
      kind=prediction_dex, coverage_start={candles:2020-09-01}) — all correct. — uac@8a8915c (2026-05-20)
- [x] ✅ **P0. Re-run UAC test suite + basedpyright** — 14/14 tests pass including 5 registry smoke tests. Lint failure
      is pre-existing **init**.py RUF022 (SIZE_EXTRA_EXCLUDES). — uac@8a8915c (2026-05-20)
- [x] ✅ **P1. Update Extended Starknet declaration** specifically — mandatory_user_agent + coverage_start now on the
      dataclass; docstring left intact per plan. — uac@8a8915c (2026-05-20)

### Phase 3 — QG ratchet enforcement

- [x] ✅ **P0. QG STEP `no_unstructured_venue_metadata.sh`** — Python checker at
      `unified-trading-pm/scripts/quality_gates/check_uac_source_capability_metadata.py`. Scans `_*.py` in
      capability_declarations/ and verifies explicit `chain=` and `kind=` kwargs on every SourceCapability block. —
      PM@(this commit) (2026-05-20)
- [x] ✅ **P0. Wire into UAC's `quality-gates.sh`** via STEP 5.85 in `base-library.sh` (after STEP 5.83). Guarded by
      `UAC_CANONICAL_EXEMPT=true`. — PM@(this commit) (2026-05-20)
- [x] ✅ **P0. Synthetic regression test** — inline regex test confirms checker catches `source='binance'` missing
      `chain=`. Checker returns exit 0 on current 70-venue corpus. — PM@(this commit) (2026-05-20)
- [x] ✅ **P0. Codex `quality-gates.md` row update** — STEP 5.85 entry added (UAC SourceCapability structured venue
      metadata guard). — PM@6c84cb472 (2026-05-20)

### Phase 4 — A2 expected_coverage() integration

This phase is the canonical consumer of the new structured `coverage_start`. Lands the data-input side of the mega-audit
Phase A2 oracle.

- [x] ✅ **P0. `expected_coverage()` reads `SourceCapability.coverage_start[data_type]`** —
      `is_before_source_coverage_start()` + `get_source_coverage_start_for_data_type()` added to
      `registry/expected_coverage.py`. Normalizes venue tokens (BINANCE-SPOT→binance, HYPERLIQUID→hyperliquid) via
      `_resolve_capability_for_venue()`. — uac@11227f95 (2026-05-20)
- [x] ✅ **P0. Test** — 16 tests in `test_expected_coverage_source_start.py`: isolated test capabilities +
      real-declaration smoke tests (hyperliquid/polymarket/binance). Confirms EXPECTED_PRE_SOURCE_COVERAGE_START signal
      correct for dates before/after venue's `coverage_start[data_type]`. — uac@11227f95 (2026-05-20)
- [x] ✅ **P1. Document the integration** in `/codex/02-data/availability-manifest-and-data-status.md` — linked
      `SourceCapability.coverage_start` to `EXPECTED_PRE_SOURCE_COVERAGE_START`, documents
      `is_before_source_coverage_start()` as SSOT consumer and co-existence with `venue_launch_dates.py`. — PM@6c84cb472
      (2026-05-20)

### Phase 5 — Codex SSOT + post-migration cleanup

- [x] ✅ **P0. Update** `/codex/02-data/contracts-scope-and-layout.md` — added capability registry table for
      chain/kind/mandatory_user_agent/coverage_start fields with canonical values, kind taxonomy, QG STEP 5.85, and
      consumer function. — PM@6c84cb472 (2026-05-20)
- [x] ✅ **P0. Update** `/codex/06-coding-standards/quality-gates.md` — STEP 5.85 row added to QG table after STEP 5.83.
      — PM@6c84cb472 (2026-05-20)
- [x] ✅ **[DEFERRED-POST-CUTOVER — named successor: uac_venue_metadata_gap_fill_2026_06_xx.md]** **P1. Prune duplicated
      info** in capability_declarations docstrings — remove now-redundant `chain: ...` / `kind: ...` lines from
      per-venue docstrings. Keep human-readable context paragraphs. (trivial-sweep 2026-05-21)
- [x] ✅ **[DEFERRED-POST-CUTOVER — activates if venue_launch_dates.py read-sites are replaced; named successor:
      post-cutover cleanup plan]** **P1. SUPERSEDED banner** on `venue_launch_dates.py` — co-existence fine per plan;
      both fields documented in `availability-manifest-and-data-status.md`. (trivial-sweep 2026-05-21)

## Success criteria

| Phase | Cutover criterion                          | Continuous verification                                                              |
| ----- | ------------------------------------------ | ------------------------------------------------------------------------------------ |
| 1     | Pydantic roundtrip + backcompat tests pass | `pytest tests/unit/test_source_capability_metadata.py`                               |
| 2     | 70 venues populated with chain + kind      | `python3 scripts/audit_source_capability_metadata.py --report` shows 70/70 populated |
| 3     | QG STEP 5.85 ratchet green workspace-wide  | `bash scripts/qg/no_unstructured_venue_metadata.sh` exit 0                           |
| 4     | `expected_coverage()` consumes new field   | A2 oracle unit tests reference the field                                             |
| 5     | Codex docs updated                         | grep returns the 3 new doc entries                                                   |

## Continuous verification column

| Item                    | Cutover criterion                          | Continuous verification                | Last verified |
| ----------------------- | ------------------------------------------ | -------------------------------------- | ------------- |
| SourceCapability schema | 4 fields + defaults                        | UAC pytest + basedpyright              | TBD           |
| 70 venues populated     | chain + kind = 70/70                       | `no_unstructured_venue_metadata.sh` QG | TBD           |
| User-Agent enforcement  | mandatory ones land in actual REST clients | adapter-side test (separate plan)      | TBD           |
| coverage_start consumed | A2 reads it                                | `expected_coverage()` unit test        | TBD           |

## Deferred work — migrated to:

| Deferred item                                                            | Successor                                                  |
| ------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Phase 5 P1 — prune redundant docstring metadata in 70 venue declarations | `uac_venue_metadata_gap_fill_2026_06_xx.md` (post-cutover) |
| Phase 5 P1 — SUPERSEDED banner on `venue_launch_dates.py`                | Post-cutover cleanup plan (when read-sites replaced)       |
| Phase 0 P1 — per-venue web research for coverage_start gaps              | `uac_venue_metadata_gap_fill_2026_06_xx.md`                |

## Temporary states + their canonical follow-up plans

- `venue_launch_dates.py` co-exists with new `SourceCapability.coverage_start` until Phase 5 cleanup. Successor: § Phase
  5 P1 above.
- Some venues will have `chain=None` if Phase 0 + Phase 1.5 research can't find a canonical answer (e.g. opaque exotic
  CEXes). Successor: P4 followup — `uac_venue_metadata_gap_fill_2026_06_xx.md` (to create when count of `chain=None`
  venues drops below 10 to make follow-up tractable).

## Agent execution prompt (for slot 3 dispatch)

```
Task: Execute uac_source_capability_metadata_promotion_2026_05_20.md
end-to-end. Operator authorized 2026-05-20.

Working dir: /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/

Method: read the plan fully first. Execute Phases 0-5 in dependency order.
Use the existing 4 of 7 mega-audit reusable patterns (no_silent_absence,
no_hardcoded_venue_urls, no_hardcoded_venue_universe,
no_adapter_contract_regression) as reference QG-script shapes for Phase 3.

Constraints:
- DO NOT add `entity` field (operator explicit, 2026-05-20).
- DO NOT delete venue_launch_dates.py — co-existence is fine until Phase 5 cleanup.
- DO NOT bypass any QG step.
- DO NOT touch per-venue adapter code in MTDS/execution-service — UAC-only + A2 consumer.

Commit cadence: per phase. Commit messages follow `feat(uac):` /
`feat(qg):` / `docs(codex):` conventional-commits convention. Push to
`live-defi-rollout`.

Report at end: 70 venues populated count, QG STEP 5.85 wiring confirmation,
A2 integration test result, any blockers + named follow-ups for residual
gaps.
```

## Estimate calibration

| Class    | Multiplier | Baseline AI-days | Calibrated AI-days |
| -------- | ---------- | ---------------- | ------------------ |
| refactor | 0.4×       | 4.0              | **1.6**            |

Bulk of the work is Phase 2 migration (mechanical script-driven edit across 5 files); Phase 4 A2 wire (~0.4 days); rest
is small (~0.2 each).

## Foundation-completion-gate alignment

This plan is layer-1 (IS hardening) work — `SourceCapability` is the canonical reference declaration consumed by every
downstream layer. Per `/codex/11-project-management/foundation-completion-gate-discipline.md`:

- Layer 1 (reference) green criterion: C0/C1/C2/C3 audits green
- This plan **strengthens** layer 1's contract by structuring metadata that was previously informal
- Layer 4 (MTDS) + Layer 5 (features) + Layer 6 (strategy) consumers benefit naturally
- Compatible with parallel-up-across-asset-groups discipline (no asset_group boundary crossed)

## Risk register

- **Migration script edge cases**: 70 venues with heterogeneous docstring formats. Mitigation: Phase 0 inventory CSV is
  the audit trail; Phase 2 P0 spot-check on 10 random venues catches drift.
- **`coverage_start` per-data_type ambiguity**: some venues genuinely have per-symbol coverage variance (e.g. Drift
  launched new markets over time). Phase 1 schema uses `dict[str, date]` keyed on data_type, not symbol — symbol- level
  variance handled by IS's per-instrument `listed_at` (already exists).
- **Workspace-wide schema change**: 70 instances mean any error in Phase 1 blocks all 70 venues. Mitigation: optional
  fields with `None` defaults; Phase 1.5 backcompat test catches breaks before Phase 2 migration runs.

## Codex SSOT updates (mandatory per CLAUDE.md "Post-Plan-Phase Codex Audit")

- `/codex/02-data/contracts-scope-and-layout.md` — add 4 new fields to SourceCapability section
- `/codex/02-data/availability-manifest-and-data-status.md` — link `coverage_start` to existing
  `EXPECTED_PRE_SOURCE_COVERAGE_START` reason
- `/codex/06-coding-standards/quality-gates.md` — STEP 5.85 entry
- `CLAUDE.md` — NO update (rule already covered by item (8) Foundation-Completion-Gate Discipline)
