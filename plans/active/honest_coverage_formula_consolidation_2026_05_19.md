---
name: honest_coverage_formula_consolidation_2026_05_19
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
status: in-flight
parent_plan: master_to_live_defi_2026_05_23.md
---

# Honest-Coverage Formula Consolidation — 2026-05-19

> **Trigger**: 2026-05-19 backfill-fleet launch revealed the data-status numerator/denominator
> was inconsistent across writegate-endtoend, expected-unattempted-propagation, and
> data-status-drilldown plans, AND the instruments-service launcher hardcoded `--force` so
> the manifest-driven skip never actually fired in production. Operator directive: "fix the
> plan complete it for manifest and deployment api/ui and service data status so that no
> confusion again and ensure the production code for IS and MTDS looks at the right
> numerator and denominator when skipping and that running without --force works."

## The Canonical Formula (SSOT — DO NOT REDEFINE ELSEWHERE)

```python
from unified_api_contracts.canonical.crosscutting.honest_coverage import (
    CaptureStatusCounts, compute_honest_coverage, HONEST_COVERAGE_GAP_FIELDS,
)

counts = CaptureStatusCounts(
    captured=...,
    empty_confirmed=...,
    attempted_failed=...,
    expected_unattempted_known_empty=...,   # error_reason startswith "EXPECTED_"
    expected_unattempted_pending_fetch=..., # error_reason NOT startswith "EXPECTED_"
)
ratio = compute_honest_coverage(counts)
# numerator   = captured + empty_confirmed + expected_unattempted_known_empty
# denominator = numerator + attempted_failed + expected_unattempted_pending_fetch
# returns 1.0 if denominator == 0
```

Equivalent in English: a slot is **honestly answered** if we have any truthful answer
(data landed, OR confirmed empty, OR Tier-3 sentinel pre-resolved as known-empty per an
`EXPECTED_*` reason). A slot is a **gap** only if we tried and failed (`attempted_failed`)
or if the sentinel says "expected, never tried" (non-`EXPECTED_*` `expected_unattempted`).

**Backfill skip rule (without `--force`)**: retry `attempted_failed` +
`expected_unattempted_pending_fetch`; skip everything else. With `--force`: refetch all,
including already-captured (operator-only escape hatch for schema migrations etc).

## Why this plan exists — formula drift inventory

Three plans each carried a partial formula with implicit numerator semantics:

| Plan | Implicit formula | Drift |
| --- | --- | --- |
| `writegate_honest_coverage_endtoend_2026_05_06.md` | "denominator clipped to legitimately-coverable shards" — pre-launch/holiday rows excluded from BOTH | OK if `empty_confirmed` is the only credit; mute on `expected_unattempted` split |
| `expected_unattempted_propagation_chain_2026_05_12.md` | Phase 2.A: `expected_unattempted` rows propagate but counting role unspecified | Missing: `EXPECTED_*` vs non-`EXPECTED_*` split |
| `data_status_drilldown_shard_atom_alignment_2026_05_07.md` | Line 170-171: "numerator = manifest rows with `capture_status=captured`" | Excludes `empty_confirmed` from numerator → understates coverage |
| `deployment-api/data_status_service.py` | Formula scattered across 350+ helper lines, no canonical expression | No grep target for QG audit |

Net result: deployment-ui sometimes showed coverage % that didn't match `--operation=status`
CLI output that didn't match what the CI ratchet would compute (if it existed).

## Status — Phase 0 shipped 2026-05-19

- [x] **P0-0a. ✅ UAC**: `compute_honest_coverage()` + `CaptureStatusCounts` NamedTuple
      land as canonical SSOT — `unified-api-contracts@327fec6`. Validates against sports
      manifest real data (100.00%). Includes `HONEST_COVERAGE_GAP_FIELDS` for the two
      gap-state field names so backfill orchestrators don't re-derive the gap set.
- [x] **P0-0b. ✅ deployment-service**: `launch-instruments-backfill-vm.sh` `--force` made
      opt-in (was hardcoded ON, defeating manifest skip) — `deployment-service@d673323`.
      Without `--force`: `MODE: --force OFF (default) — manifest-driven skip ACTIVE` printed
      at launch. Re-launched 7 VMs at 19:54 UTC in no-force mode; manifest will filter.
- [x] **P0-0c. ✅ deployment-service**: EXIT-trap log upload across 14 inline-script VM
      launchers — `deployment-service@6b4610c`. New helper `lc_log_upload_trap_block` in
      `lib/launcher_common.sh` emits a snippet that tees stdout+stderr to `/var/log/run.log`
      and installs a `trap EXIT` handler uploading to canonical
      `gs://deployment-scripts-<project>/vm-logs/<vm-name>/run.log` with 3-attempt retry.
      Fires on success, error, signal, `set -e` propagation. Closes the demonstrated
      mtds-solana-drift-backfill bug (TERMINATED with no log uploaded). Unblocks Phase 8
      verification — post-mortem on any failed VM now always has evidence.

## Pre-Audit Before Execution (per Citadel-Grade Planning Standards)

Workspace-wide consumers of the legacy formula(s) that need migration to
`compute_honest_coverage()`:

```bash
# Run from workspace root to enumerate all callers requiring migration:
rg -l "captured.*total|coverage.*pct|honest_coverage|_coverage_ratio" \
   --type py --glob '!.venv*' --glob '!build' --glob '!tests'
```

Expected hits per audit:

1. `deployment-api/deployment_api/services/data_status_service.py` — primary panel rollup
2. `deployment-api/deployment_api/services/data_status_drilldown_service.py` — drilldown
3. `instruments-service/instruments_service/api/data_status_endpoint.py` (or similar)
4. `market-tick-data-service/.../api/data_status_endpoint.py`
5. `deployment-ui/src/.../DataStatusPanel.tsx` (or `unified-trading-system-ui/src/...`)
6. Per-service `--operation=status` CLI handlers (count: TBD by Phase 2/3 sub-agent)

QG addition (Phase 6) blocks any new caller that recomputes the formula inline rather
than importing `compute_honest_coverage`.

## Phased Execution DAG

```
Phase 0 (✅ DONE)
   │
   ├── Phase 1 (UTL helper)  ─┐
   │                          │
   ├── Phase 2 (IS migration) ┤
   │                          ├── Phase 4 (deployment-api) ─── Phase 5 (UI) ─── Phase 6 (CI ratchet)
   ├── Phase 3 (MTDS migr.)   ┤
   │                          │
   └─ Phase 7 (codex docs)  ──┘                                                   │
                                                                                  └── Phase 8 (verify on real fleet)
```

### Phase 1 — UTL `ManifestWriter.read_capture_status_counts()` helper

- [ ] **P0. UTL helper**: in `unified-trading-library/unified_trading_library/manifest_writer.py`
      (or a sibling reader module — pick whichever the existing API uses for reads), add
      `read_capture_status_counts(bucket: str, *, asset_group: str, data_type: str | None = None,
      date_range: tuple[date, date] | None = None) -> CaptureStatusCounts`. Reads the manifest
      parquet, groups rows by `(capture_status, error_reason)`, applies the
      `EXPECTED_*` split rule, returns the typed counts. **Why UTL not UAC**: UAC is
      schema-only; manifest READS are UTL's job.
- [ ] **P0. Test**: roundtrip — write a synthetic manifest with all 4 statuses + a mix of
      `EXPECTED_*` and non-`EXPECTED_*` reasons; assert counts split correctly.
- [ ] **P1. Per-service docstring rule**: every service's `/api/data-status` endpoint
      MUST call this helper, not re-implement the manifest read.

### Phase 2 — instruments-service migration

- [ ] **P0. CLI `--operation=status`**: replace whatever bespoke counting it does with
      `read_capture_status_counts()` → `compute_honest_coverage()` → JSON output. Output
      shape: `{"asset_group": ..., "data_type": ..., "counts": {...all 5 fields...},
      "coverage": <float>}`.
- [ ] **P0. Skip path for `--force=false`**: confirm `vm_instruments_backfill.sh`
      orchestrator.py:1310 + 1465 skip logic skips `captured` + `empty_confirmed` +
      `expected_unattempted_known_empty`, but DOES retry `attempted_failed` +
      `expected_unattempted_pending_fetch`. Patch if it misses the split semantics.
- [ ] **P1. /api/data-status endpoint**: same migration for the HTTP endpoint.

### Phase 3 — MTDS migration (parallel with Phase 2)

- [ ] **P0. Same migration as Phase 2** but for `market-tick-data-service`. Audit found
      orchestrator.py:1985 already skips when `force=False`; confirm it honors the
      EXPECTED_*/non-EXPECTED_* split too.
- [ ] **P0. Per-data-type CLIs**: lending-indices, lst-rates, dex-pools, perp-funding,
      etc. — each must respect the no-force skip rule via the shared helper, not re-derive.

### Phase 4 — deployment-api consumers

- [ ] **P0. `data_status_service.py`**: replace the scattered helper functions with one
      call to `compute_honest_coverage()` per (asset_group, data_type) panel cell.
      Remove the ~350 lines of inline numerator/denominator math.
- [ ] **P0. `data_status_drilldown_service.py`**: same migration for shard-level drilldown.
- [ ] **P1. API response shape**: every endpoint returns
      `{"counts": CaptureStatusCounts.as_dict(), "coverage": float}` so the UI never has
      to re-derive.

### Phase 5 — deployment-ui consumers

- [ ] **P0. `DataStatusPanel.tsx`**: render `counts` + `coverage` directly from API
      response. Remove any client-side aggregation. Display all 5 fields in the drilldown
      tooltip (not just captured/total).
- [ ] **P1. Coverage % color thresholds**: define one threshold set workspace-wide
      (green ≥99%, amber 95-99%, red <95% per master plan).

### Phase 6 — CI ratchet

- [ ] **P0. `honest-coverage-ratchet.sh`** in `unified-trading-pm/scripts/qg/`: snapshot
      yesterday's coverage per asset_group × data_type, compare to today, fail QG if any
      ratio regressed by >0.5pp. Stored snapshot: `_index/snapshots/honest_coverage/`.
- [ ] **P0. QG STEP wired**: per-service `quality-gates.sh` calls the ratchet for that
      service's bucket scope.
- [ ] **P1. Inline-formula linter**: `grep` for re-implementations of the formula in any
      file outside `honest_coverage.py` → QG FAIL.

### Phase 7 — Codex docs

- [ ] **P0. Update** `codex/02-data/availability-manifest-and-data-status.md` § "Coverage
      formula" — point to `compute_honest_coverage()` as the SOLE SSOT.
- [ ] **P0. Add SUPERSEDED banner** to the 3 in-flight plans' inline formula sections
      pointing here.
- [ ] **P1. Update** `codex/02-data/honest-absence-downstream-handling.md` § "Reason
      taxonomy" — note that consumers MUST check the EXPECTED_*/non-EXPECTED_* split when
      computing coverage, not just `capture_status` alone.

### Phase 8 — verify on real fleet

- [ ] **P0. Re-pull manifest counts** for instruments-service + all 5 MTDS asset_groups
      after Phase 0b backfills complete (2026-05-20 ETA). Apply `compute_honest_coverage()`.
      Goal: every (asset_group, data_type) cell reports a real number. Cells reporting
      100% with 0 `expected_unattempted_pending_fetch` rows are SUSPICIOUS — denominator
      may be incomplete (Tier-3 sentinel propagation Phase 3D.5 pending per
      `expected_unattempted_validation_pending_phase3_2026_05_19.md`).
- [ ] **P0. Master plan update**: add Group H "Path to 99% coverage" row with the
      continuous-verification path = `honest-coverage-ratchet.sh` daily run + this plan's
      Phase 8 sweep result.

## Downstream Consumer Updates

Every consumer of legacy coverage math:

| Consumer | File | Migration | Owner phase |
| --- | --- | --- | --- |
| deployment-api panel | `data_status_service.py` | replace inline math | Phase 4 |
| deployment-api drilldown | `data_status_drilldown_service.py` | replace inline math | Phase 4 |
| deployment-ui panel | `DataStatusPanel.tsx` | use API value | Phase 5 |
| instruments-service /api/data-status | `api/data_status_endpoint.py` (TBD) | use UTL helper | Phase 2 |
| instruments-service `--operation=status` CLI | TBD | use UTL helper | Phase 2 |
| MTDS /api/data-status | TBD | use UTL helper | Phase 3 |
| MTDS per-data-type CLIs | TBD | use UTL helper | Phase 3 |
| QG ratchet | `unified-trading-pm/scripts/qg/honest-coverage-ratchet.sh` (NEW) | call `compute_honest_coverage` | Phase 6 |

## Continuous Verification Column (per Master Plan rule)

| Item | Cutover criterion | Continuous verification | Last verified |
| --- | --- | --- | --- |
| Formula SSOT | UAC export + 1 test | `pytest tests/canonical/crosscutting/test_honest_coverage_formula.py` (Phase 1) | 2026-05-19 (manual roundtrip in REPL) |
| No-force skip works | Backfill on already-captured asset_group runs in <10min | Phase 0b VM logs; daily ratchet | 2026-05-19 (in-flight on instr-backfill-* VMs) |
| Consumer parity | API + UI + CLI report same coverage | QG STEP 5.XX (Phase 6) | TBD |

## Codex SSOT updates (mandatory per HARD RULE)

Touched in Phase 7:

- `codex/02-data/availability-manifest-and-data-status.md`
- `codex/02-data/honest-absence-downstream-handling.md`
- `codex/06-coding-standards/manifest-skip-semantics.md` (NEW — codifies no-force skip rule)

## Temporary states + their canonical follow-up plans

- The legacy inline formulas in `data_status_service.py` continue working until Phase 4
  ships. New code MUST use `compute_honest_coverage`. Plan's Phase 4 is the cleanup
  successor; pre-existing inline math is review-blocking on touch.

## Deferred work after 2026-05-19 honest-coverage consolidation session

| Item | Reason | Successor plan |
| --- | --- | --- |
| Phases 1-8 implementation | Multi-repo, multi-day scope; not bundleable into May-19 session | This plan (Phases 1-8) |
| Tier-3 sentinel propagation completion | Pre-existing — Phase 3D.5 pending | `expected_unattempted_validation_pending_phase3_2026_05_19.md` |
| `measure-honest-coverage.py` baseline script | Pre-existing TBD per master plan audit | `master_to_live_defi_2026_05_23.md` Group H (new) |
