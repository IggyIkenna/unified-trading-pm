---
name: api_football_phase_3b_3c_smoke_forward_poll
overview: |
  Execute api_football Phase 3.B + 3.C — live-API smoke test and EPL forward-poll
  verification of the flattened normalizers (shipped Phase 1-3 on 2026-05-08).
  Verify per-row output shape matches expected column count + row grain; verify
  features-sports calculators can read the new schema without NaN bloat.
type: code
status: active
created: 2026-05-13
deadline: 2026-05-14 EOD
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

> **🟢 RESERVE WORK — pulled from api_football_minimal_flattening_removal_2026_05_07**
>
> Phases 1-3 shipped on 2026-05-08. Phase 3.B + 3.C are operator-driven live-API + forward-poll verification steps
> marked DEFERRED. This plan re-scopes them as reserve work for execution when capacity allows.

# Context

Phases 1-3 of
[api_football_minimal_flattening_removal_2026_05_07](api_football_minimal_flattening_removal_2026_05_07.md) shipped on
2026-05-08 by Tab 5:

- **Phase 1**: UAC normalizer functions (`normalize_api_football_fixture_stats`, `_fixture_event`, `_lineup`, `_injury`)
  rewritten to return `list[dict]` for per-team/per-event/per-player row explosion ✅
- **Phase 2**: UAC SchemaContracts extended from 2-column minimal to 10-23 columns per data_type ✅
- **Phase 3 code**: instruments-service handlers updated to wire `chain.from_iterable` across normalizer outputs ✅
- **Phase 3.B + 3.C**: Smoke tests (live-API + EPL forward-poll) marked DEFERRED pending operator credentials ⏳ **THIS
  PLAN**

All code is shipped and locally tested (integration smoke verified 2 stat rows / 3 event rows / 29 lineup rows / 1
injury row). This plan executes the operational verification on real infrastructure.

## Phased execution

### Phase 3.B — Live-API smoke test (1–2 hours, 🔴 BLOCKER: API credentials)

**Blockers:**

- API-Football API key required (available via act-secrets but credential access needed at runtime)
- Need a recently-played fixture af_fixture_id from captured FIXTURES parquet

**Steps:**

1. **Locate a recent fixture** (15 min)
   - Query `gs://instruments-store-sports-prod/asset_group=sports/data_type=match/fixtures/latest/`
   - Pick one `af_fixture_id` from last 7 days (e.g., EPL match from 2026-05-06 to 2026-05-13)

2. **Create recovery-fixture-ids parquet** (15 min)
   - Write minimal parquet with single row: `{"af_fixture_id": "<picked_id>"}`
   - Upload to `gs://instruments-store-sports-prod/_smoke_test/recovery_fixtures.parquet` or local

3. **Invoke recovery-mode handler** (30 min)

   ```bash
   cd /repo/instruments-service
   DEPLOYMENT_ENV=prod \
   API_FOOTBALL_API_KEY=$(get-act-secret api_football_key) \
   instruments-service \
     --operation instruments \
     --mode batch \
     --asset-group sports \
     --venues API_FOOTBALL \
     --recovery-fixture-ids gs://instruments-store-sports-prod/_smoke_test/recovery_fixtures.parquet \
     --start-date 2026-05-06 \
     --end-date 2026-05-13 \
     --sports-entity API_FOOTBALL_FIXTURES \
     --log-level INFO
   ```

4. **Verify parquet schema + row count** (30 min)
   - Load output parquets via pyarrow
   - Assertion: FIXTURE_STATS has ~18 columns (not 2) + 2 rows (per-team)
   - Assertion: FIXTURE_EVENTS has ~10 columns + ~15 rows (per-event)
   - Assertion: FIXTURE_LINEUPS has ~13 columns + ~22 rows (per-player)
   - Assertion: FIXTURE_INJURIES has ~11 columns
   - Log results + flip checkbox with evidence

---

### Phase 3.C — EPL forward-poll verification (2–4 hours)

**Prerequisites:**

- Phase 3.B complete (validates normalizers + handlers work)
- VM tarball refresh (code @ live-defi-rollout)
- API-Football credentials
- deployment-ui on localhost:5183 or prod

**Steps:**

1. **Refresh VM tarball** (15 min)
   - `bash deployment-service/scripts/vm/create-code-tarballs.sh --sports-only` OR auto-trigger via launcher
   - Verify tarball @ `gs://deployment-scripts-${PID}/code/`

2. **Launch EPL forward-poll VM** (10 min)
   - `bash deployment-service/scripts/vm/launch-sports-instruments-reference-vm.sh --asset-group sports --start-date 2026-05-13 --end-date 2026-05-13`
   - VM boots, downloads tarball, runs instruments-service

3. **Monitor execution** (1–2 hours wall clock)
   - Watch `gs://${PROJECT_ID}-events/events/instruments-service/` for `INSTRUMENT_ENTITY_CAPTURED` events
   - Abort on `ADAPTER_FETCH_FAILED` errors

4. **Verify data-status panel schema** (30 min)
   - Open deployment-ui → Data Status → Sports → Match → Fixtures
   - Click Schema modal: FIXTURE_STATS should show ~18 columns (not old 2-column schema)
   - Screenshot for evidence

5. **Spot-check features-sports calculator** (30 min)
   - If calculators exist (e.g., `shots_on_target_advantage`, `xg_delta`):
     - Load features-sports pipeline for same EPL day
     - Verify columns that depend on fixture_stats are populated (not NaN)
   - If no calculator yet: skip (separate plan owns feature-consumer work)

---

## Full-execution criteria

- ✅ **Phase 3.B**: Recovery-mode handler invoked on one fixture, output parquet schema verified
  - **What ran**: instruments-service CLI with `--recovery-fixture-ids` on 1 recent EPL fixture
  - **Verification**: pyarrow schema inspection shows full column count + expected row grain

- ✅ **Phase 3.C**: EPL forward-poll completed, data-status panel verified
  - **What ran**: `launch-sports-instruments-reference-vm.sh` for 2026-05-13, VM executed end-to-end
  - **Verification**: INSTRUMENT_ENTITY_CAPTURED events in bucket + data-status modal shows ~18 columns for
    FIXTURE_STATS

---

## Risks + mitigations

| Risk                                             | Mitigation                                                                                |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| API-Football rate limit exceeded                 | Use `--recovery-fixture-ids` to limit to 1 fixture (Phase 3.B); single day for Phase 3.C  |
| VM tarball stale (code not on live-defi-rollout) | Ensure all changes pushed before launching; use `create-code-tarballs.sh --all` if unsure |
| Features-sports calculators not yet written      | Phase 3.C spot-check is optional; skip if no calculator exists (separate plan owns that)  |
| Event stream transient failures                  | Fall back to manifest + parquet inspection if event stream unreliable                     |

---

## Notes

- **Temporary state**: Historical thin parquets (before 2026-05-08) remain until Phase 4 reprocessor OR forward-poll
  naturally overwrites. Acceptable per original plan § "Temporary states"; features calculators have NaN gates.
- **Phase 5 plan closeout** deferred until Phase 3.B+3.C ship. Original plan `locked_by: live-defi-rollout` status
  survives.
- **Credentials**: API_FOOTBALL_API_KEY available via `gh secret view API_FOOTBALL_API_KEY` or act-secrets in CI.
- **Handoff**: If not executing this session due to credential/time constraints, this plan documents scope + blockers
  for next agent.

## Temporary states + their canonical follow-up plans

- **After Phase 3.B+3.C complete**: Phase 4 (optional reprocessor) from the parent plan remains a defer candidate
- **After Phase 5 shipped**: Plan closure + codex doc update (sports column-count expectations)
