---
name: manifest_master_audit_instructions
type: audit-instructions
epic: manifest_master
assigned_vm: vm-defi
tier: L1
last_updated: 2026-06-01
---

# Manifest Master — Audit Instructions

## Epic Scope

Manifest **v9** schema (`MANIFEST_SCHEMA_VERSION = 9` — v9 added the tradfi `source` column), 4-state `capture_status`
(`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`), honest absence (the `EmptyConfirmedReason`
closed set in UAC — **32 members** as of 2026-06-01: 28 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` + `NO_INPUT_AVAILABLE` +
`LEG_ABSENT_LEFT` + `LEG_ABSENT_RIGHT`; always read the enum, never trust this count), cluster validation at
`record_captured()`,
`available_at` semantics, single-walk discipline, and the manifest consolidator (Cloud Run + Cloud Scheduler).

Codex SSOTs: `codex/02-data/availability-manifest-and-data-status.md`,
`codex/02-data/honest-absence-downstream-handling.md`, `codex/05-infrastructure/manifest-consolidator-ssot.md`

## Triggers

- Weekly (minimum cadence)
- After every writegate phase change
- When A3 manifest divergence scan shows RED (any `DIVERGENT_EMPTY` or `MISSING_EXPECTED`)
- After any new `EmptyConfirmedReason` is added to UAC
- After manifest consolidator infrastructure changes (Cloud Run revision, Cloud Scheduler config)
- **Per-service `capture_status` write-path calibration (run as each producer service matures / BEFORE it backfills
  at scale)** — see the dedicated section below. Re-run on any producer when its emission paths change. Auditing the
  _code_ before the corpus fills means the backfill writes correct statuses; auditing after means reconciling a
  manifest with baked-in wrong statuses.

## Checklist

- [ ] (a) **Schema version in actual PROD data**: read actual `schema_version` column from prod manifest (not code
      constant). Must be ≥ 95% at **v9** (`MANIFEST_SCHEMA_VERSION = 9`) across all asset_groups. Do NOT trust the
      constant — read the data. Run: `python3 plans/audit/results/a4_manifest_v9_compliance.py` or equivalent query

- [ ] (b) **All EmptyConfirmedReason values present**: the full closed set exists in UAC (32 members as of 2026-06-01 —
      28 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` + `NO_INPUT_AVAILABLE` + `LEG_ABSENT_LEFT` + `LEG_ABSENT_RIGHT`; **count
      the enum, don't trust this number**). Read:
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

### Per-Service `capture_status` Write-Path Calibration (run per-service, as each matures)

**Purpose**: this is a CODE write-path audit, not a manifest data-search — so it is valid regardless of how much data
is backfilled. Run it per producer service so the code writes the rule-correct status BEFORE that service backfills at
scale (a status-writing bug, left unfixed, bakes wrong statuses across millions of rows; fixing the code first makes the
ongoing/remaining backfill correct as it fills). Re-runnable any time a service's emission paths change.

**Producer services in scope** (audit each as it is run / matures):
instruments-service · market-tick-data-service (MTDS) · market-data-processing-service (MDPS) ·
features-service (delta_one / volatility / cross_instrument / multi_timeframe / onchain / calendar / sports) · any other
service that calls `record_captured` / `record_empty` / `record_failed` / `record_empty_for_shard`.

> Maturity note (2026-06-01): the 3 upstream data services (IS / MTDS / MDPS) are mostly calibrated — **re-check** them.
> Downstream + less-exercised services are audited **as they are run**, before each backfills at scale.

**The decision rule (encode per write-path):**

| Real situation                                                              | Correct status                                   | Notes                                                                 |
| --------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| Data genuinely absent (holiday, no source coverage, contract not listed)    | `empty_confirmed` + typed `EmptyConfirmedReason` | **LAST resort** — only after all other possibilities ruled out        |
| Upstream produced nothing but SHOULD have (not downloaded yet, dep not ready) | NOT `empty_confirmed` → dependency-gate skip / `expected_unattempted` | data is **owed**: retry / backfill, never confirm-empty |
| Attempted and errored (fetch / backfill error)                              | `attempted_failed` (+ `stack_trace`)             | transient/real failure, not an absence                                |
| Wrote rows                                                                  | `captured`                                       | normal                                                                |

**Per-service procedure:**

- [ ] **Enumerate every emission path** in the service — every `record_captured` / `record_empty` /
      `record_failed` / `record_empty_for_shard` call AND every code path that returns without writing any manifest row.
      Grep: `rg "record_(captured|empty|failed|empty_for_shard)" <service>/ --include="*.py"`.
- [ ] **Anti-pattern 1 — reflexive `empty_confirmed`**: for each `record_empty` callsite, confirm the code has *ruled
      out* "data owed" first (dependency present? source actually returned zero vs not-yet-downloaded?). A
      `record_empty` reached on a missing-upstream / not-backfilled branch is a **silent correctness lie** → must be a
      dependency-gap skip / `attempted_failed` instead.
- [ ] **Anti-pattern 2 — silent no-row skip**: any in-scope shard that can `return` / `continue` without writing a
      manifest row is indistinguishable from a crash → must write a typed status (no silent skips).
- [ ] **Spot+future corollary**: a future cannot exist without a spot for its underlying. For paired features
      (`futures_basis` etc.), "future present, spot absent" is a contradiction (bug); the only legitimate absence is
      "spot present, future absent" (future not listed for that underlying in that window → `empty_confirmed`, typed).
- [ ] **Typed reason check**: every `empty_confirmed` carries a real `EmptyConfirmedReason` (never blank — composes with
      checklist (c)/(d) above).
- [ ] **Wire a QG guard where feasible**: a silent no-row for an in-scope shard should fail QG for that service.
- [ ] **Record findings** per producer in the result file; fix the real bugs in the owning service repo before/while it
      backfills.

Known live instances (genesis of this audit, 2026-05-27): delta_one 4h/24h missing-1h-dependency (now correctly
fast-fails — textbook "data owed" ≠ empty); volatility `futures_basis` silent-skip when future leg absent (features now
emits `empty_confirmed(SOURCE_RETURNED_ZERO)` on no-input — verify the listed-vs-not-downloaded distinction).
Genesis: operator-raised 2026-05-27; principle + instances folded inline above (this section is the everlasting home).

## Success Criteria

- All 8 checklist items GREEN
- Per-service `capture_status` write-path calibration GREEN for every producer that has been run/matured (no reflexive
  `empty_confirmed` on owed-data branches, no silent no-row skips)
- A3 manifest divergence: zero `DIVERGENT_EMPTY` + zero `MISSING_EXPECTED` across all asset_groups
- QG exits 0 for all services (cluster validation step passes everywhere)

## Output Format

Result file at `plans/audit/results/manifest_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
