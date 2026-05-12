# Slot 4 — Ping Ledger

Intra-side ping ledger for Slot 4 (propagation chain Phases 0–4 + MDPS 4-state contract + Script-1 root-cause).
Bidirectional: main → slot 4 and slot 4 → main.

---

## [slot 4 → main] Gate 0A fired: UAC Phase 0A + UTL Phase 0B complete

**Timestamp**: 2026-05-12 **Status**: ✅ GATE 0A CONDITION MET

Phase 0A: `uac@0457b0e` — `EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` added to
`EmptyConfirmedReason` (20 total members). Pushed to `live-defi-rollout`.

Phase 0B: `read_availability_index(bucket: str)` at `manifest_writer.py:3257` already accepts arbitrary upstream
buckets. No new helper needed. Downstream services call it directly with upstream bucket name. Existing tests in
`test_manifest_completeness.py` cover mock-GCS paths.

**Gate 0A condition satisfied** — Phases 1, 1.5, 2, 3, 4 may proceed.

Proceeding directly to Phase 1 (MTDS pre-flight wired to instruments-service manifest).

---

## [slot 4 → main] Phase 2 ✅ complete; Phase 3 AWAITING OPERATOR DIRECTION

**Timestamp**: 2026-05-12 **Status**: 🟡 PHASE 3 DESIGN DECISION NEEDED

### Phase 2 shipped (MDPS record_expected_unattempted on dep-skip)

- `mdps@3f70cf6` — `record_expected_unattempted_for_shard` in `canonical_writer.py` + `_record_expected_unattempted_on_skip`
  wired into `process_category` dep-skip path. 4 unit tests in `test_expected_unattempted_on_dep_skip.py` — all pass.
- `pm@5ab28423` — codex `honest-absence-downstream-handling.md` § "MDPS downstream consumption contract" added (4-state table).
- All Phase 2 checkboxes flipped.

### Phase 3 design blocker

`InstrumentDomainConfig.subscription_list` is **runtime-loaded from GCP config** (DomainConfigReloader), NOT a static
frozenset that can be grepped and put in UAC. Three options in plan § "Phase 3.0":
- **Option A** (preferred): runtime comparison at batch_handler startup — get instruments from instruments-service catalog,
  compare with runtime subscription_list, write `expected_unattempted` for out-of-scope. No UAC constant needed.
- **Option B**: static extract from GCP config → UAC frozenset (fragile, staleness risk).
- **Option C**: inline comparison per-module, no UAC constant.

**Request**: operator direction on Phase 3.0 option before slot 4 implements Phase 3.1–3.N.

### Pre-existing MDPS test failures (FINDING — not caused by Phase 2)

19 pre-existing test failures in MDPS before Phase 2 work:
- `test_canonical_writer_ohlcv_1h_policy.py` — 15 failures: `EmissionDecision.__init__()` missing 2 new required args
  (`service_emission_state` + `last_emission_decision_at`) from a recent UTL update. UTL added these fields; MDPS tests
  still instantiate old signature. Root cause: UTL `EmissionDecision` class schema drift.
- `test_sports_adapters.py` — `DRAFTKINGS` not in `['ODDS_API', 'PINNACLE', 'BETFAIR']` — sports config changed.
- `test_cli_main.py` — `STARTUP_VALIDATION_FAILED: Invalid env ENVIRONMENT='test'` — UAC validation tightened.
- `test_check_shard_freshness_granular_rows_only.py` — data_type freshness logic drift.

All confirmed pre-existing (existed before my Phase 2 changes). Flagging for operator triage — owner unknown, likely
the writegate Phase 6.x / EmissionDecision owners.

---

## [main → slot 4] Phase 3.0 direction: Option A

**Timestamp**: 2026-05-12 **Status**: ✅ OPERATOR DIRECTION GIVEN

**Phase 3.0 → Option A confirmed.** Runtime comparison at batch_handler startup using instruments-service catalog.
Rationale: `subscription_list` is runtime-loaded from GCP DomainConfigReloader by design — hardcoding to UAC (Option B)
creates staleness risk and violates dynamic-config intent. Inline per-module (Option C) duplicates logic. Option A is
correct: at batch_handler startup, fetch the expected instrument set from instruments-service catalog, compare with
runtime `subscription_list`, write `expected_unattempted` for anything in the catalog that's out-of-scope. No UAC
constant needed. Proceed with Phases 3.1–3.N on Option A.

**MDPS test failures**: 19 pre-existing failures noted. The `EmissionDecision` schema drift (15 tests, 2 missing required
args: `service_emission_state` + `last_emission_decision_at`) is a **cross-side finding** — UTL changed the signature,
MDPS tests not updated. Filing cross-side ping to Harsh now. Slot 4 should NOT fix these in this session (foreign scope
— UTL change owner unknown; likely Harsh writegate team). Sports/CLI/freshness failures also pre-existing; defer to
their plan owners. **Slot 4: proceed with Phase 3 assuming test failures are pre-existing baseline; your Phase 2 work is
clean.**
