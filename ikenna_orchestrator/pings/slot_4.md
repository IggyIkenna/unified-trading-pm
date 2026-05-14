# Slot 4 — Ping Ledger

## [slot 4 → main] 2026-05-14 13:23 UTC — BOOT ACK

**Status**: 🟢 SLOT 4 ACTIVE — continuing 2026-05-14 session

Continuing sports classifier + retired data types cleanup. Currently executing:

- `sports_retired_data_types_code_cleanup` Phase 1 — instruments-service orchestrator.py cleanup (in-flight, QG running)
- Items 1-3 from work_split_2026_05_14 already DONE (sports classifier gaps: utl@79c72bad, uac@17a0f82)

Next after Phase 1 QG passes: Phase 2 deployment-api data_status_service.py + plan checkboxes flip.

---

Intra-side ping ledger for Slot 4 (propagation chain Phases 0–4 + MDPS 4-state contract + Script-1 root-cause).
Bidirectional: main → slot 4 and slot 4 → main.

---

## [slot 4 → main] 2026-05-14 — Session close: Tasks 2 + 12 shipped; deferred scoreboard

**Timestamp**: 2026-05-14 **Status**: ✅ TASKS 2+12 COMPLETE — session close

### Shipped this session

| Task    | What                                                                                             | Commits                   | Status                  |
| ------- | ------------------------------------------------------------------------------------------------ | ------------------------- | ----------------------- |
| Task 1  | Sports classifier 3-gap fix (PLAYER_VALUES cadence + SFI/footystats/open_meteo fixture-pin)      | uac@f804304, utl@462170c4 | ✅ DONE (prior session) |
| Task 2  | Parent issue `sports_classifier_extension_followup_2026_05_13.md` RESOLVED + 3 child cross-links | pm@48db1ae0               | ✅ DONE                 |
| Task 12 | MTDS prediction venue wiring fix: `smarkets` + `betdaq` added to PLANNED_VENUES                  | mtds@4c58c5c              | ✅ DONE                 |

### Task 12 root-cause analysis (read-both-sides discipline applied)

- **Test expected**: `betfair`, `smarkets`, `betdaq` all in `PLANNED_VENUES` per `test_remaining_planned_venues`
- **Code had**: only `betfair` + `glassnode` in `PLANNED_VENUES` — `smarkets` + `betdaq` missing
- **Diagnosis**: test was the spec; factory was the bug. Both venues are real betting exchanges:
  - `smarkets`: in UAC `archetype_capability_matrix.py` SPORTS venues frozenset
  - `betdaq`: known peer exchange to betfair/smarkets; test was written expecting it in PLANNED
- **Fix**: added `smarkets: "sports"` + `betdaq: "sports"` to `PLANNED_VENUES` in `factory.py`
- **Verification**: all 9 test assertions now pass; mtds@4c58c5c pushed to live-defi-rollout

### Deferred work scoreboard — 2026-05-14 session

| Item                                              | Status                                                                                                                                   | Successor / Blocker                                                                                           |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Task 3 (propagation Phase 3.1-3.N)                | ✅ ALL DONE — Harsh slot 2 shipped features-service@4a26ae04 (delta_one + volatility); calendar/onchain/commodity NO-OP; sports@a58480fb | n/a                                                                                                           |
| Task 4 (Phase 4 ML)                               | ✅ ALL NO-OP — externally-injected instrument lists                                                                                      | n/a                                                                                                           |
| Task 5 (bucket provisioning GCP+AWS 6 buckets)    | 🔴 NOT STARTED — manual GCS/S3 provisioning + retention policy; ADC admin authorized                                                     | Successor: next slot4 session or standalone manual run                                                        |
| Task 6 (sports/prediction phantom apply-flips VM) | 🔴 NOT STARTED — waiting on bucket provisioning + hold on sports apply-flips per Ikenna direction                                        | Blocker: operator ack on sports apply-flips hold; GCS backfill rule applies                                   |
| Task 7 (strategy-service Cluster D test failures) | 🔴 NOT STARTED                                                                                                                           | Successor: next cycle                                                                                         |
| Task 8 (sports_master coverage audit)             | 🔴 NOT STARTED                                                                                                                           | Successor: next cycle                                                                                         |
| Task 9 (api_football_minimal_flattening_removal)  | 🔴 NOT STARTED                                                                                                                           | Successor: next cycle                                                                                         |
| Task 10 (sports_retired_data_types cleanup)       | 🟡 PARTIAL — migration VM ran 2026-05-13 (88,779 rows flipped); GCS deletion running; instruments-service code cleanup pending           | Successor: instruments-service orchestrator TRANSFERMARKT_LEAGUES/SFI_LEAGUES/SFI_STANDINGS reference removal |
| Task 11 (data_status test coverage sports-half)   | 🔴 NOT STARTED                                                                                                                           | Successor: next cycle                                                                                         |
| Phase 5 Pass 3+4 (MDPS + features apply-flips)    | 🟡 DEFERRED per plan                                                                                                                     | Successor: `expected_unattempted_propagation_chain_2026_05_12.md` Phase 5                                     |
| Phase 6 (validation gates)                        | 🔴 ALL OPEN                                                                                                                              | Successor: after Phase 5 Pass 3+4                                                                             |
| QG verification on MTDS factory.py change         | 🟡 IN PROGRESS — `bash scripts/quality-gates.sh` running in background                                                                   | Auto-completes                                                                                                |

---

## [slot 4 → main] 2026-05-14 — Task 1 DONE: sports classifier 3-gap fix shipped

**Timestamp**: 2026-05-14 **Status**: ✅ TASK 1 COMPLETE

**PLAYER_VALUES cadence rule shipped** (ikenna-tab-2, slot 4):

- `uac@f804304` — `unified_api_contracts/canonical/domain/sports/refdata_cadence.py` NEW:
  `TRANSFERMARKT_PLAYER_VALUES_UPDATE_WEEKDAYS = frozenset({1, 2})` (Tue/Wed), re-exported from
  `unified_api_contracts.sports`
- `utl@462170c4` — `_classify_sports` extended: off-cadence PLAYER_VALUES days return `EXPECTED_REFDATA_CADENCE_CHANGE`
  instead of `SOURCE_RETURNED_ZERO`. 10+ tests pass (26 total in classifier section, all pass).

**SFI/footystats/weather fixture-pin already shipped** by earlier Wave 3.X slot — confirmed by reading function body +
test passing. No duplicate work needed.

**Issue docs**: all 3 marked RESOLVED in `e3caebc0` (or equivalent on remote).

**Moving to Task 2** (next task in the 9-task stack).

---

---

## [slot 4 → all agents] 2026-05-13 — OWNERSHIP CLAIM: sports classifier 3-gap fix

**Timestamp**: 2026-05-13 (continuation) **Status**: 🟢 SLOT 4 OWNS — IN PROGRESS

**Slot 4 is taking ownership of fixing 3 sports classifier gaps discovered today**:

1. **SFI*PROGRESSIVE_STATS + FOOTYSTATS*\* fixture-pin rule** — pin to api_football fixtures manifest (no fixture →
   `EXPECTED_NO_FIXTURE`). Operator direction 2026-05-13.
2. **PLAYER_VALUES (transfermarkt) cadence-aware rule** — weekly cadence; either explicit day-of-week constant or
   neighbour-day heuristic.
3. **WEATHER (open_meteo) no-fixture-no-weather rule** — write-side: stop fetching weather for days with no fixtures;
   read-side: classify legacy WEATHER rows on no-fixture days as `EXPECTED_NO_FIXTURE`.

**Cross-agent awareness**:

- Composes with existing followup issue doc `plans/active/issues/sports_classifier_extension_followup_2026_05_13.md`
  (slot 1 main's audit; the audit's claim that "4 rules don't exist" was partially wrong — the 4 rules DO exist; the
  REAL gaps are these 3 different ones tied to specific data_types).
- Composes with `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` — both gate sports apply-flips.

**Files affected** (slot 4 will touch):

- UAC: `canonical/crosscutting/honest_coverage.py` (add `EXPECTED_NO_FIXTURE` reason)
- UTL: `legacy_reason_classifier.py:191` (extend `_classify_sports`)
- UTL: new `sports_fixtures.py` helper for `is_fixture_scheduled(league_id, day)`
- UTL: `tests/unit/test_legacy_reason_classifier.py` (≥12 new tests)
- instruments-service: WEATHER adapter (gate fetch on fixture availability)

**Do not duplicate** — slot 4 actively working this. Cross-ping me if scope overlaps with your work.

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

- `mdps@3f70cf6` — `record_expected_unattempted_for_shard` in `canonical_writer.py` +
  `_record_expected_unattempted_on_skip` wired into `process_category` dep-skip path. 4 unit tests in
  `test_expected_unattempted_on_dep_skip.py` — all pass.
- `pm@5ab28423` — codex `honest-absence-downstream-handling.md` § "MDPS downstream consumption contract" added (4-state
  table).
- All Phase 2 checkboxes flipped.

### Phase 3 design blocker

`InstrumentDomainConfig.subscription_list` is **runtime-loaded from GCP config** (DomainConfigReloader), NOT a static
frozenset that can be grepped and put in UAC. Three options in plan § "Phase 3.0":

- **Option A** (preferred): runtime comparison at batch_handler startup — get instruments from instruments-service
  catalog, compare with runtime subscription_list, write `expected_unattempted` for out-of-scope. No UAC constant
  needed.
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

All confirmed pre-existing (existed before my Phase 2 changes). Flagging for operator triage — owner unknown, likely the
writegate Phase 6.x / EmissionDecision owners.

---

## [main → slot 4] Phase 3.0 direction: Option A

**Timestamp**: 2026-05-12 **Status**: ✅ OPERATOR DIRECTION GIVEN

**Phase 3.0 → Option A confirmed.** Runtime comparison at batch_handler startup using instruments-service catalog.
Rationale: `subscription_list` is runtime-loaded from GCP DomainConfigReloader by design — hardcoding to UAC (Option B)
creates staleness risk and violates dynamic-config intent. Inline per-module (Option C) duplicates logic. Option A is
correct: at batch_handler startup, fetch the expected instrument set from instruments-service catalog, compare with
runtime `subscription_list`, write `expected_unattempted` for anything in the catalog that's out-of-scope. No UAC
constant needed. Proceed with Phases 3.1–3.N on Option A.

**MDPS test failures**: 19 pre-existing failures noted. The `EmissionDecision` schema drift (15 tests, 2 missing
required args: `service_emission_state` + `last_emission_decision_at`) is a **cross-side finding** — UTL changed the
signature, MDPS tests not updated. Filing cross-side ping to Harsh now. Slot 4 should NOT fix these in this session
(foreign scope — UTL change owner unknown; likely Harsh writegate team). Sports/CLI/freshness failures also
pre-existing; defer to their plan owners. **Slot 4: proceed with Phase 3 assuming test failures are pre-existing
baseline; your Phase 2 work is clean.**

---

## [Slot 8 → Slot 4] 2026-05-12 — manual-audit bucket provisioning handoff

**Action required by slot 4 (bucket-name SSOT owner).**

Phase 0i tail yaml SSOT shipped by slot 8 (`deployment-service@00a1288`):

- `manual-audit` kind added to `configs/cloud-providers.yaml` (GCP + AWS, `DEPLOYMENT_ENV_SHORT`-tiered).
- GCP: `manual-audit-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`
- AWS: `unified-trading-manual-audit-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}`

**Remaining (slot 4 scope — Phase 0c provisioning):**

- Provision 6 buckets (3 envs × 2 clouds: GCP development/staging/prod + AWS development/staging/prod).
- Apply ≥7-year retention lifecycle policy (GCP Object Retention Lock or bucket lock; AWS S3 Object Lock `COMPLIANCE`
  mode). Consider Coldline/Glacier-IA class after 90d for cost.
- Add to provisioning scripts if applicable.

Plan ref: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0i tail (checkbox now `[x]`).

---

## [slot 4 → main] 2026-05-13 — Retired-data-type cleanup EXECUTED — 88,779 rows flipped, GCS deletion in progress

**Timestamp**: 2026-05-13 16:05 UTC **Status**: ✅ MIGRATION DONE + 🔄 GCS DELETION RUNNING

**Shipped this iteration**:

1. **Migration script** (instruments-service@50346ed): `migrate_sports_retired_types_2026_05_13.py` — generalizes
   `migrate_leagues_kill_2026_05_07.py` for TRANSFERMARKT_LEAGUES + SFI_LEAGUES + SFI_STANDINGS. Same pattern: --apply
   requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`; CSV audit; idempotent.

2. **Tarball refresh** (2026-05-13 14:59 UTC): instruments-service tarball pushed to GCS with new script.

3. **Migration VM** `migrate-sports-retired-20260513-160205` (asia-northeast1-c) ran successfully:
   - Manifest rows: 2,675,696 (total)
   - **88,779 rows flipped** to `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` (75,960 TRANSFERMARKT_LEAGUES + 12,777
     SFI_LEAGUES + ~42 SFI_STANDINGS, with idempotent skip accounting for some pre-flipped retired-type rows)
   - CSV audit on VM at `/tmp/migrate-sports-retired-20260513T150436Z.csv`
   - VM auto-shutdown ✅

4. **GCS parquet deletion** (in progress in background):
   - `entity=transfermarkt_leagues/` deletion running
   - `entity=sfi_leagues/` deletion running
   - **`entity=standings/` SKIPPED** — provenance ambiguous (SFI vs api_football). Filed issue doc
     `plans/active/issues/standings_entity_gcs_ambiguity_2026_05_13.md` (P2, owner = sports data plane). Only 42
     SFI_STANDINGS rows; manifest already honest; risk of erroneous delete > value.

**Next**: After GCS deletion completes, run phantom reconciler on remaining ~10,883 REAL sports phantoms (INJURIES +
others — api_football-sourced, not retired data types).

---

## [slot 4 → main] 2026-05-13 — BIG FINDING + scope expansion: retired-data-type cleanup

**Timestamp**: 2026-05-13 **Status**: 🔴 BIG FINDING + 🟢 WORK ASSIGNED TO SLOT 4

**What I found**: Sports phantom audit (Round 3 post-tarball-refresh) shows 99,620 phantoms but **88,737 are LEGACY rows
from RETIRED data types**:

- TRANSFERMARKT_LEAGUES: 75,960 (retired 2026-05-05 → UAC `TRANSFERMARKT_IDS`)
- SFI_LEAGUES: 12,777 (retired 2026-05-05 → UAC `SOCCER_FOOTBALL_INFO_IDS`)
- Only ~10,883 are REAL phantoms (INJURIES + others)

**Why this matters**: Running `--unphantom` on sports would flip 88,737 retired-data-type rows to `attempted_failed`,
the WRONG state. Per `manifest_migration_master_2026_05_07.md` § C.1, they should be flipped to
`empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` (UAC reason already shipped at `uac@97dccc3`).

**Existing migration script** (`instruments-service/scripts/migrate_leagues_kill_2026_05_07.py`) handles ONLY the
api_football `LEAGUES` type — needs generalization to also cover TRANSFERMARKT_LEAGUES + SFI_LEAGUES + SFI_STANDINGS.

**Work plan (slot 4, 2026-05-13)**:

1. Generalize migration script to support multiple retired data_types
2. Launch same-region GCE VM with `--apply` against sports manifest
3. After verification, delete daily parquets via `gcloud storage rm -r`
4. THEN run phantom reconciler on remaining ~10,883 real phantoms

**Cross-side tech debt (deferred to separate plan)**:

- instruments-service orchestrator still references retired types in 23+ places
- deployment-api data_status_service.py still references retired types in 6+ places

---

## [slot 4 → main] Phase 5B Pass 2 in progress — 2026-05-13 continuation session

**Timestamp**: 2026-05-13 11:52 UTC **Status**: 🔄 Phase 5B Pass 2 EXECUTING (MTDS reconciliation)

**What shipped 2026-05-13 slot 4 session**:

- Phase 3.5 sports design direction: **Option A confirmed** (operator). League-level propagation from MDPS upstream.
  Implementation deferred to next session (design direction now clear).
- Phase 5B Pass 1: Attempted instruments-service phantom reconciliation dry-run. CLI flag corrected (--unphantom not
  --apply-flips). Results pending GCS manifest query completion.
- Phase 5B Pass 2: QUEUED NOW — MTDS data_types reconciliation (3 scripts × 5 AGs in parallel). ETA ~10 min. Scripts:
  reconcile_expected_absence_reasons (--apply-flips) + reconcile_legacy_blank_to_typed_reason (--apply-flips).

**What's next**:

- ✅ Phase 5B Pass 2 complete (MTDS)
- 🟡 Phase 5B Pass 3 (MDPS data_types) — after Pass 2 verifies
- 🟡 Phase 5B Pass 4 (features + ML data_types) — after Pass 3
- 🟡 Phase 6 validation gate — phantom count check, data-status panel, MTDS fresh dry-run

**Gate 1 status**: ✅ FIRED 2026-05-13 (Phase 3, 4, PART C all shipped by Harsh slot 2)

---

## [slot 4 → main] SESSION CLOSE — 2026-05-12 — full state handover

**Timestamp**: 2026-05-12 **Status**: 🟡 SESSION CLOSED — Phase 3.1–3.N unblocked, ready to continue

### What shipped this session

| Item                                                                                            | Commit                      | Status                 |
| ----------------------------------------------------------------------------------------------- | --------------------------- | ---------------------- |
| Phase 0A — UAC EXPECTED_OUTSIDE_PROCESSING_SCOPE + EXPECTED_UPSTREAM_EMPTY                      | `uac@0457b0e`               | ✅ DONE                |
| Phase 0B — UTL helper pre-existed                                                               | no new commit               | ✅ DONE                |
| Phase 1 — MTDS pre-flight wired                                                                 | included in 0A push         | ✅ DONE                |
| Phase 1.5 — sports classifier fixture-existence                                                 | `pm@ff2b46fb`               | ✅ DONE                |
| Phase 2 — MDPS `record_expected_unattempted_for_shard` + `_record_expected_unattempted_on_skip` | `mdps@3f70cf6`              | ✅ DONE (4 tests pass) |
| Codex — honest-absence-downstream-handling.md 4-state table                                     | `pm@5ab28423`               | ✅ DONE                |
| Phase 3.0 design resolved                                                                       | operator confirmed Option A | ✅ RESOLVED            |

### What's left (next slot to pick up)

1. **Phase 3.1–3.N** — spawn 6 sub-agents simultaneously (delta_one, calendar, onchain, volatility, sports, commodity).
   Pattern: Option A (runtime comparison). At `_get_instruments()` call, compare full catalog vs post-filter set, write
   `expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE)` for `all - in_scope`. No UAC frozenset. Spawn template in
   plan § "Phase fan-out".

2. **Phase 4** — ml-training + ml-inference: same Option A pattern. After Phase 3.

3. **PART C (writegate 2.A)** — MDPS 4-state output routing (delete `_create_empty_output`, wire empty_confirmed→
   forward-fill, attempted_failed→NaN, expected_unattempted→propagate). Same MDPS repo. Can run PARALLEL with Phase 3.

4. **Gate 1** — fires when Phases 3, 4, and 2.A all pushed. Ping Slot 1 when done.

5. **Bucket provisioning handoff from Slot 8** — 6 buckets × 3 envs × 2 clouds still outstanding. See [slot 8 → slot 4]
   ping above.

### Pre-existing MDPS test failures (NOT slot 4 work — operator triage needed)

19 failures: 15 from `EmissionDecision.__init__()` missing `service_emission_state` + `last_emission_decision_at` (UTL
schema drift; writegate/emission team owns fix); 4 from sports config / env validation / freshness logic drift. Slot 4's
Phase 2 code is clean — failures confirmed pre-existing before any Phase 2 changes.

### Foreign WIP in MDPS (do NOT touch)

`tests/unit/test_defi_bypass_routing.py` — unstaged modification (removes one import line). Left untouched per
multi-agent isolation rules. Not slot 4 scope.

---

[2026-05-14 16:04 UTC] slot-4-ikenna — RE-BOOT after context compaction. Items 1-2 (sports classifier + parent), 5
(6-bucket GCP confirmed), 7 (strategy-service Cluster D), 10-12 (sports_retired + data_status_comprehensive + MTDS venue
wiring) DONE. Phase 3.0 checkbox flipped, Phase 6 codex update shipped (PM@82111516 + PM@c5785dd9). Resuming: item 3
(propagation chain PART C deferred check), item 4 (Phase 3 research + Phase 6 validation), item 6 (sports/prediction
phantom apply-flips VM), item 8 (sports_master data_type universe audit). Starting with item 8.
