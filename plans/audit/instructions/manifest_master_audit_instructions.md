---
name: manifest_master_audit_instructions
type: audit-instructions
epic: manifest_master
assigned_vm: vm-defi
tier: L1
last_updated: 2026-05-22
---

# Manifest Master — Audit Instructions

## Epic Scope

Manifest v8 schema, 4-state `capture_status` (`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`),
honest absence (17 `EXPECTED_*` reasons + `SOURCE_RETURNED_ZERO`), cluster validation at `record_captured()`,
`available_at` semantics, single-walk discipline, and the manifest consolidator (Cloud Run + Cloud Scheduler).

Codex SSOTs: `codex/02-data/availability-manifest-and-data-status.md`,
`codex/02-data/honest-absence-downstream-handling.md`, `codex/05-infrastructure/manifest-consolidator-ssot.md`

## Triggers

- Weekly (minimum cadence)
- After every writegate phase change
- When A3 manifest divergence scan shows RED (any `DIVERGENT_EMPTY` or `MISSING_EXPECTED`)
- After any new `EmptyConfirmedReason` is added to UAC
- After manifest consolidator infrastructure changes (Cloud Run revision, Cloud Scheduler config)

## Checklist

- [ ] (a) **Schema version in actual PROD data**: read actual `schema_version` column from prod manifest (not code
      constant). Must be ≥ 95% at v8 across all asset_groups. Do NOT trust the constant — read the data. Run:
      `python3 plans/audit/results/a4_manifest_v8_compliance.py` or equivalent query

- [ ] (b) **All EmptyConfirmedReason values present**: 17 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` exist in UAC. Read:
      `unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason` — count members

- [ ] (c) **No blank reason strings**: no `record_empty(reason="")` or `record_empty(reason=None)` anywhere. Grep:
      `rg 'record_empty\(reason=""' --include="*.py"` — must be 0 hits Grep:
      `rg 'record_empty\(reason=None' --include="*.py"` — must be 0 hits

- [ ] (d) **LegacyBlankErrorReasonError not suppressed**: no `except LegacyBlankErrorReasonError: pass` or equivalent.
      Grep: `rg "LegacyBlankErrorReasonError" --include="*.py"` — verify it is raised, not silently caught

- [ ] (e) **Cluster validation at record_captured() — QG STEP 5.64**: cluster\_\* kwargs present at every bundled
      `record_captured()` call. UTL raises `MissingClusterValidationError` if absent — verify this fires in tests. Run:
      QG STEP 5.64 passes for all services

- [ ] (f) **available_at is write-time per-row**: no service derives `available_at` at read time. Grep:
      `rg "available_at.*datetime.now\|available_at.*utcnow" --include="*.py"` — should be 0 hits at read paths Verify:
      UTL `record_captured` asserts presence internally

- [ ] (g) **Single-walk discipline**: no plan or code change proposes a new whole-corpus GCS walk without
      migration-window operator ack. Grep: `rg "walk.*gcs\|gcs.*walk" plans/active/ --include="*.md"` — review any hits
      for compliance

- [ ] (h) **Manifest consolidator runtime**: Cloud Run + Cloud Scheduler running (10 jobs, `*/1 * * * *`). Check:
      `gcloud run jobs list --region asia-northeast1` — verify consolidator jobs present Verify: legacy GCE VM launcher
      (`launch-manifest-consolidator-vm.sh`) does NOT exist. Grep:
      `rg "launch-manifest-consolidator-vm" --include="*.sh"` — should be 0 hits

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Success Criteria

- All 8 checklist items GREEN
- A3 manifest divergence: zero `DIVERGENT_EMPTY` + zero `MISSING_EXPECTED` across all asset_groups
- QG exits 0 for all services (cluster validation step passes everywhere)

## Output Format

Result file at `plans/audit/results/manifest_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
