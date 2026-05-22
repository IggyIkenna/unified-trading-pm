---
name: batch_live_symmetry_master_audit_instructions
type: audit-instructions
epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-05-22
---

# Batch=Live Symmetry Master — Audit Instructions

## Epic Scope

Per-service batch=live audit across all 19 epic code surfaces. Reconciliation scripts. The invariant: batch and live
are operational modes of the SAME pipeline — identical schemas, data_types, fields. Banned: separate live-only
data_types; distinct field sets; `available_at` derived at read-time.

Codex SSOTs: `codex/02-data/service-output-emission-semantics.md`,
`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`

## Triggers

- Monthly (minimum cadence)
- After any new adapter ships (must verify both modes present)
- When A3 manifest divergence shows `DIVERGENT_EMPTY` (batch/live parity gap)
- After any writegate phase change

## Checklist

- [ ] (a) **Batch adapter count == live adapter count**: for every service and every asset_group.
      Run: `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — report any gaps (batch_count ≠ live_count)

- [ ] (b) **No standalone live-only data_types**: every data_type that exists in `--mode live` also exists in
      `--mode batch` for the same service.
      Grep: `rg "mode.*live\|live.*only" --include="*.py"` — review any hits for data_type isolation

- [ ] (c) **No distinct field sets between live and batch**: the schema for each data_type is identical regardless of mode.
      Check: `a1_scan_codified_shape_compliance.py` output — no schema divergence between modes

- [ ] (d) **available_at not derived at read-time**: no adapter sets `available_at` from `datetime.now()` or equivalent
      at the point of consumption/reading.
      Grep: `rg "available_at.*datetime.now\|available_at.*utcnow" --include="*.py"` — should be 0 hits in live
      adapters (write-time derivation only is permitted)

- [ ] (e) **All services have --mode batch and --mode live in CLI**: every service CLI exposes both modes.
      Grep: `rg "\-\-mode.*batch|\-\-mode.*live" --include="*.py"` across all service entry points

- [ ] (f) **a6 script runs clean**: `a6_batch_live_adapter_parity.py` produces a report with no unclassified rows
      (every adapter is either "paired" or "BLOCKED-CREDENTIALS").
      Run: `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — zero unclassified rows

## Success Criteria

- All 6 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows 100% adapter parity (every batch adapter has a live counterpart)
- A3 manifest divergence: zero `DIVERGENT_EMPTY` across all services

## Output Format

Result file at `plans/audit/results/batch_live_symmetry_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date | Result file | Status |
|------|-------------|--------|
| (populated as audits run) | | |
