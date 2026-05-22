---
name: mtds_mdps_master_audit_instructions
type: audit-instructions
epic: mtds_mdps_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-05-22
---

# MTDS / MDPS Master — Audit Instructions

## Epic Scope

Market Tick Data Service (MTDS) all adapters (23 batch + 18 live as of 2026-05-20), MDPS candles, writegate, raw market
data pipeline. Key invariants: QG STEPS 5.64 (cluster validation), 5.66 (per-VM shard isolation), 5.69 (bucket name
SSOT), honest absence, batch=live adapter parity.

Codex SSOTs: `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`codex/02-data/availability-manifest-and-data-status.md`, `codex/05-infrastructure/gcs-object-operations.md`

## Triggers

- Weekly (minimum cadence)
- After each new MTDS adapter ships
- After any writegate phase change
- When A3 manifest divergence scan shows `DIVERGENT_EMPTY` or `MISSING_EXPECTED`
- After VM tarball deployment to update batch adapter coverage

## Checklist

- [ ] (a) **ADAPTER_FETCH_FAILED emitted**: every adapter emits `ADAPTER_FETCH_FAILED` event on all error paths. Grep:
      `rg "ADAPTER_FETCH_FAILED" market-tick-data-service/ --include="*.py"` — count vs adapter file count; every
      handler file should have at least one hit

- [ ] (b) **Cluster validation at record_captured() — QG STEP 5.64**: mandatory `cluster_*` kwargs present at every
      `record_captured()` call for bundled data_types. Run: `bash scripts/quality-gates/cluster_validation.sh` (or
      equivalent QG step)

- [ ] (c) **Per-VM shard isolation — QG STEP 5.66**: `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true` wired. Run: relevant QG
      step; grep for `MANIFEST_PER_VM_SHARDS` in VM launch scripts

- [ ] (d) **Bucket lookup via resolve_bucket_name() — QG STEP 5.69**: no inline `gs://` f-strings. Run:
      `bash scripts/quality-gates/no_inline_bucket_fstrings.sh` (or equivalent) Grep:
      `rg "gs://" market-tick-data-service/ --include="*.py"` — should be 0 hits in business logic

- [ ] (e) **Batch adapter count == live adapter count**: parity across all asset_groups. Run:
      `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — report any gaps

- [ ] (f) **EmptyConfirmedReason for empty returns**: all adapters that can return empty data use a typed reason from
      `UAC EMPTY_CONFIRMED_REASONS`; no blank strings. Grep:
      `rg 'record_empty\(reason=""' market-tick-data-service/ --include="*.py"` — should be 0 hits

- [ ] (g) **Manifest schema_version in actual data**: read actual `schema_version` column from a sample of prod manifest
      rows (not the code constant). Must be ≥ 95% at current version (v8 as of 2026-05-20). Run:
      `python3 plans/audit/results/a4_manifest_v8_compliance.py` — check actual distribution

- [ ] (h) **No subprocess gsutil/gcloud for per-object ops**: all per-object GCS operations use UTL library. Grep:
      `rg "subprocess.*gsutil|subprocess.*gcloud" market-tick-data-service/ --include="*.py"` — should be 0 hits

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
- `a6_batch_live_adapter_parity.py` shows 100% parity (batch count == live count per venue per asset_group)
- A3 manifest divergence: zero `MISSING_EXPECTED` and zero `DIVERGENT_EMPTY`
- QG exits 0 for market-tick-data-service

## Output Format

Result file at `plans/audit/results/mtds_mdps_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
