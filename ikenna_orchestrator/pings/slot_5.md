# Slot 5 Pings

---

## [slot 5 → main] Phase 2.D PART A — complete (2026-05-12)

**Status**: ✅ SHIPPED (both repos pushed to live-defi-rollout / tab/ikennaigboaka/5)

**Commits**:

- `unified-api-contracts@0a3d464` — feat(sports): Phase 2.D UAC — match timing fields, source latency constants,
  PST/CANC reasons
- `instruments-service@9bffca2` — feat(sports): Phase 2.D instruments-service — match timing fields, PST/CANC wiring, 5
  unit tests

**What shipped**:

1. ✅ UAC `CanonicalFixture`: `match_end_time` / `announced_at` / `report_time` (optional datetime fields)
2. ✅ UAC `EmptyConfirmedReason`: `EXPECTED_FIXTURE_POSTPONED` + `EXPECTED_FIXTURE_CANCELLED`
3. ✅ UAC `registry/source_data_latency.py`: p95 lag constants for SFI/Understat/FootyStats/API-Football/Open-Meteo
4. ✅ UAC `external/api_football/normalize.py`: `announced_at = kickoff_utc - 7 days`
5. ✅ SFI adapter: `detect_match_end_time()` + `_MIN_MATCH_END_RUN` constant (freeze-detect + batch max-timer path)
6. ✅ Orchestrator: `_af_record_empty` extended with `reason=` param; PST/CANC elif →
   `record_empty(EXPECTED_FIXTURE_POSTPONED/CANCELLED)`
7. ✅ Orchestrator: `_flatten_canonical_fixture_for_disk` extended with 3 new timing fields
8. ✅ Tests: 5 unit tests in `test_phase2d_match_timing.py` + updated `_EXPECTED_COLUMNS` in flattener test

**Deferred (not in Phase 2.D scope as shipped)**:

- ❌ `report_time` derivation in instruments-service write path: `detect_match_end_time()` exists but not yet called
  from the SFI progressive stats write path to populate `report_time` on the CanonicalFixture object
- ❌ `assert_available_at_present` wiring (spawn prompt step 8)
- ❌ Tests cannot be executed: pre-existing broken import `get_expected_bookmakers` in `canonical/domain/__init__.py`
  imports from `bookmaker_registry` but was moved to `bookmaker_accessors.py` (foreign modified file). All
  instruments-service tests blocked.

**Big finding — bookmaker_registry import broken**:

- `unified-api-contracts/unified_api_contracts/canonical/domain/__init__.py:266` imports `get_expected_bookmakers` from
  `bookmaker_registry`
- `bookmaker_registry.py` is foreign-modified (visible in `git status`); has comment at line 868:
  "get_expected_bookmakers lives in bookmaker_accessors.py"
- Fix: change `domain/__init__.py:266` to `from .sports.bookmaker_accessors import get_expected_bookmakers`
- **This is foreign code — owner should fix.**

**PART B status**: Waiting for cross-tab ping from defi_recursive Phase 2 design close.

---

## [slot 5 → main] SESSION CLOSE 2026-05-12 — sports_master work complete + handover

**Status**: ✅ SESSION CLOSED — all code pushed, plans updated, scoreboard written

### What shipped this session (all on live-defi-rollout)

- `instruments-service@af06124` — `detect_match_end_time()` + `report_time` wired into SFI progressive-stats
  write path (per-row `match_end_time` + `report_time` ISO string columns); also fixed push refspec bug
  (needed `HEAD:live-defi-rollout` not `live-defi-rollout`)
- `unified-api-contracts@1a831b0` — `MatchStatus` canonical StrEnum SSOT
  (`unified_api_contracts/canonical/domain/sports/fixture_status.py`): 9 states, `AF_STATUS_SHORT_MAP`,
  `from_af_short()`, `COMPLETED_STATUSES` / `IN_PROGRESS_STATUSES` / `TERMINAL_STATUSES` / `PRE_MATCH_STATUSES` /
  `AF_COMPLETED_CODES`; exported from domain `__init__`

### Plan flips committed (PM)

- B.1 Phases 1+2+3+5 → `[x]` (Harsh's UAC@c76e6d0 + IS@539130f retroactively credited)
- C.6 DEFERRED report_time → `[x]` (instruments-service@af06124)
- MatchStatus StrEnum SSOT item → `[x]` (UAC@1a831b0, adapter migration DEFERRED)

### LDR sync performed

- All 3 repos rebased onto latest `live-defi-rollout` during session
- UAC `honest_coverage.py` conflict resolved: kept all 4 new members
  (`EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` from LDR +
  `EXPECTED_FIXTURE_POSTPONED` + `EXPECTED_FIXTURE_CANCELLED` from slot 5)
- UAC `domain/__init__.py:266` broken `get_expected_bookmakers` import was ALREADY fixed by LDR (foreign agent)
  before we merged — no action needed

### Session-close deferred scoreboard

Full table in `plans/epics/sports_master_2026_05_07.md` § "Deferred work after 2026-05-12 slot-5 session".

**Best next-agent entry points** (no blockers):
1. C.7 Follow-up #3 MATCHES `team_a_*` → `home_*` field mapping fix (FootyStats normalizer quick win)
2. C.4 Transfermarkt per-player `normalize_player_values` flatten (self-contained UAC + IS)
3. C.6 Step 2 `SFI_PROGRESSIVE_STATS` contract columns (UAC-only schema addition)

---

## [main → slot 5] bookmaker BIG FINDING resolved + deferred items acked + PART B unblocked

**Timestamp**: 2026-05-12 **Status**: ✅ RESOLVED (bookmaker) + ✅ ACKED (deferred items)

**Bookmaker BIG FINDING → RESOLVED**: Slot 2 (defi-catalogue) shipped UAC@`b73949d` which fixed
`canonical/domain/__init__.py:266` — `get_expected_bookmakers` now imports from `bookmaker_accessors.py` (not
`bookmaker_registry`). Pull latest LDR in your UAC worktree (`git fetch` + rebase) to get this fix; your
instruments-service tests should unblock immediately.

**Phase 2.D deferred items** — operator ack:
- `report_time` derivation not wired: ✅ Confirmed deferred. Add as `- [ ]` todo in `sports_master` or
  the instruments-service plan before closing Phase 2.D in your slot.
- `assert_available_at_present` wiring: ✅ Deferred to Phase 2.E or sports_master carry-forward. Neither blocks PART B.

**PART B (Phase 2.C features-sports stubs)**: PART B depends on your OWN `defi_recursive_borrow_archetypes`
Phases 1-2 design closing (not a cross-slot gate). If defi_recursive Phases 1-2 are done, proceed to PART B now.
Spawn prompt for PART B is in `work_split_2026_05_12_ikenna.md` at the Slot 5 section. If defi_recursive Phases 1-2
are still in flight, continue that work — PART B queues behind it within your slot.

**`test_sports_adapters.py` DRAFTKINGS failure**: Pre-existing sports config change — not caused by your Phase 2.D.
Leave as pre-existing baseline; do NOT block your session on it.
