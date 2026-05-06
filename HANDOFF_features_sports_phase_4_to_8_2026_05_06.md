# HANDOFF — features-sports honest-coverage Phase 4-8 (2026-05-06)

You are picking up the **features-sports honest-coverage** project after Phase 0.6 → Phase 3.E1

- Phase 8.B (drift detector) all shipped to `origin/live-defi-rollout`. The architecture is in place end-to-end; the
  remaining work is **operational** (Phase 4-7 backfills) and **UI surface** (Phase 8.A). Phase 8.B (drift comparator)
  is done; only the cron entrypoint + dashboard wiring is left under Phase 8.

**Workspace root:** `/Users/ikennaigboaka/Code/unified-trading-system-repos/` **Active branch:** `live-defi-rollout`
**Plan:** `unified-trading-pm/plans/active/features_sports_honest_coverage_2026_05_05.plan.md`

---

## ⚠ Read these BEFORE writing any code

1. `unified-trading-system-repos/.claude/CLAUDE.md` — workspace rules, especially **Honest absence vs fake
   placeholders**, **No fire-and-forget VM launches**, **Manifest concurrency principle**, **Sports source coverage
   windows**, and the new **Shard-granularity SSOT** + **VIX 15m source layering** sections.
2. `unified-trading-pm/plans/active/features_sports_honest_coverage_2026_05_05.plan.md` — the active plan with phase
   outcomes + Phase 0.6.G follow-ups.
3. `unified-trading-pm/plans/active/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — parallel stream;
   coordinate with that agent before touching `ManifestWriter` / `record_captured` / write-gate code in UTL.
4. The 11 commits this session shipped (table below) — read commit messages for design context.

---

## ✅ What's done (DO NOT redo)

| Commit     | Repo                    | Phase                                                                                                                           |
| ---------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `dacea12`  | features-sports-service | **0.6** SFI progressive halftime backfill (script + calculator + reader fixes) — 89% detection, 2073 captured + ~243 empty days |
| `de0e924d` | unified-trading-pm      | **0.6** outcomes plan — full 7-VM iteration log + Phase 0.6.G follow-ups                                                        |
| `3137271`  | unified-api-contracts   | **1** UAC SSOT: `UpstreamReq` + `FEATURE_UPSTREAM_REQUIREMENTS` (34 calculators) + `in_coverage` + 20 tests                     |
| `cf298fa`  | features-sports-service | **2 MVP** `coverage_gate` module + `CoverageVerdict` enum + 15 tests                                                            |
| `474722c`  | features-sports-service | **2.E** dispatcher wiring for Group 21+22 (sfi_progressive, footystats_predictions) + 4 integration tests                       |
| `fa7464c`  | features-sports-service | **2.E1** `_gate_then_run` helper wired into all 8 older calculator branches + 3 integration tests                               |
| `6f7771f`  | deployment-api          | **3 MVP** `_features_sports_expected_dates_for_calculator` per-feature-group helper + 7 tests                                   |
| `51bcc26`  | deployment-api          | **3.E1** `per_feature_per_league_per_fixture_date` axis branch in `_sports_honest_coverage` + 2 tests                           |
| `25f6d73`  | features-sports-service | **4 prep** `honest_coverage_report.py` operator CLI + 7 tests                                                                   |
| `9874f13`  | features-sports-service | **0.6.G.5** per-league manifest writes in `compute_sfi_progressive_only` (so per-league denominator matches)                    |
| `acd2d25`  | deployment-api          | **8.B** `coverage_drift.py` comparator + DriftEvent + 14 tests                                                                  |

**Architecture is now end-to-end:**

- UAC declares per-calculator upstream requirements (Phase 1)
- features-sports-service compute distinguishes `upstream_missing` vs `out_of_coverage` (Phase 2)
- deployment-api data-status surfaces per-calculator coverage rows (Phase 3)
- Operator CLI prints per-calc coverage from the manifest (Phase 4 prep)
- Drift comparator returns DriftEvents between two snapshots (Phase 8.B)

---

## 🚧 What's left

### Phase 4-7 — Stage A-D backfills (OPERATIONAL — requires VM launches)

The plan has 7 Stage A backfill todos (P4.A → P4.G) — one VM launch per source, in order: understat → openmeteo →
transfermarkt → soccer_football_info → footystats → api_football → odds_api. **Each one is hours of VM runtime + cost.**
Don't kick them off without explicit operator sign-off.

For each Stage A source:

1. Run the Phase 4-prep CLI to identify the gap:
   ```bash
   cd features-sports-service
   .venv/bin/python -m features_sports_service.scripts.honest_coverage_report \
       --bucket features-sports-central-element-323112 \
       --start-date 2024-01-01 --end-date 2024-12-31 \
       --calculators <calc1>,<calc2> --out gap.csv
   ```
2. Use the launcher pattern from `deployment-service/scripts/vm/launch-features-sports-backfill-vm.sh` (existing for
   FIXTURE_FEATURES) — copy to a new launcher per Stage A source.
3. **Apply the no-fire-and-forget protocol**: pair every VM launch with event-stream verification (90s STARTED check,
   periodic progress polling, STOPPED at exit).
4. After each Stage A run, verify the data-status tab reflects ≥95% coverage where the upstream is ≥95% (the gap should
   track the upstream gap, not exceed it).

**Phase 5 (Stage B per-source iteration), Phase 6 (Stage C cross-source), Phase 7 (Stage D enriched)** all follow the
same pattern but with progressively more upstream entanglement. Phase 6 in particular has cross-source joins that are
brittle — verify each calculator's output coverage ≈ intersection of (required upstreams' coverage), not less.

### Phase 8.A — UI surface (deployment-ui)

The data-status tab at
[`unified-trading-system-ui/components/ops/deployment/DataStatusTab.tsx`](../../unified-trading-system-ui/components/ops/deployment/DataStatusTab.tsx)
currently renders SPORTS coverage rows by data_type. **Wire the new `per_feature_per_league_per_fixture_date` axis** so:

1. The features-sports-service tab shows per-calculator rows (one row per of the 34 calculators in
   `FEATURE_UPSTREAM_REQUIREMENTS`) instead of the current 3-row `FIXTURE_FEATURES / ODDS_FEATURES / DERIVED_FEATURES`
   rollup.
2. Click-through drill-down: clicking a calculator row reveals per-league sub-rows showing expected/captured/missing for
   each league. The per-league data is already in `_sports_honest_coverage`'s response under `per_league` (commit
   `51bcc26`).
3. When a calculator at coverage X% has its upstream's coverage at Y%, surface the relationship: "team_xg at 60% (capped
   by understat XG at 60%, api_football FIXTURES at 95%)". The upstream attribution data is in
   `FEATURE_UPSTREAM_REQUIREMENTS` — read it from a new deployment-api endpoint that exposes the SSOT.

### Phase 8.B — Drift cron entrypoint + dashboard

The comparator is shipped (`coverage_drift.py`). What's left:

1. Daily Cloud Run job in **deployment-service** that snapshots the manifest's per-(calc, league) coverage to GCS (e.g.
   `gs://{pid}-coverage-snapshots/sports/{date}/snapshot.parquet`) — uses `read_availability_index` +
   `_coverage_per_calc_league` from `deployment_api/services/coverage_drift.py`.
2. The comparator runs against today vs N days back (default 7); emits `COVERAGE_DRIFT` structured events the operator
   dashboard subscribes to.
3. Dashboard surface in **unified-trading-system-ui** showing recent drift events.

---

## 📋 Phase 0.6.G follow-ups still open

Most are deferred from the Phase 0.6 closeout. P0.6.G.5 (per-league manifest writes) is now done (commit `9874f13`).
Remaining:

- **P0.6.G.1** Migrate SFI progressive_stats from mixed long+wide to pure wide format — touches **instruments-service**
  writer, not features-sports-service. Removes the `groupby('timer_seconds').first()` collapse in `_detect_halftime`.
- **P0.6.G.2** Bridge the af_fixture_id ↔ SFI fixture_id ID-space gap — instruments-service progressive_stats writer
  should attach `af_fixture_id` per row so cross-source joins work without `fixture_mapping.parquet`.
- **P0.6.G.3** Per-league `ht_detection_method` distribution audit — sample 50+ matchdays, surface chronically-low
  leagues (LIGA_3, AUSTRIAN_BUNDESLIGA, GREEK_SUPER_LEAGUE) in `FEATURE_UPSTREAM_REQUIREMENTS` so they're flagged
  "ht_unavailable expected".
- **P0.6.G.4** Push detection rate from 89% → 95%+ via richer freeze signals (SFI `goals` for score-stagnation;
  `attacks_normal` / `possession_pct` once P0.6.G.1 schema migration unlocks them).

---

## 🛠 Workspace conventions (CRITICAL)

- `cd <repo> && bash scripts/quality-gates.sh` for tests (uses repo `.venv`). NEVER `pytest` directly.
- `bash scripts/quickmerge.sh "msg" --agent --files <list>` is the canonical commit/push wrapper. This session used
  `git commit --no-verify + git push origin live-defi-rollout` because the prek hook silently aborted commits when
  prettier/ruff-format reformatted files mid-commit without re-staging — known issue, the operator approved the
  workaround.
- Conventional commit prefixes required: `feat(scope):` / `fix(scope):` / `docs(scope):` / `chore(scope):`.
- `from unified_api_contracts.sports import FEATURE_UPSTREAM_REQUIREMENTS, in_coverage, UpstreamReq` — Phase 1 SSOT
  lives at the sports facade.
- **Honest absence vs fake placeholders** — re-read the workspace CLAUDE.md section. `record_empty` for
  legitimately-empty source responses; `record_failed` with classified error for exceptions; raise loud for
  reader/schema-drift bugs.
- **No fire-and-forget VM launches** — every VM launch MUST pair with active event-stream verification (90s STARTED,
  periodic progress polling, STOPPED at exit). The Phase 0.6 backfill required 7 VM iterations to converge precisely
  because each iteration was monitored end-to-end.
- **Sports GCS path SSOT** — never hardcode `sports_reference/by_date/...`. Use UAC's `candidate_parquet_paths`.
- **VM tarball deployment** — `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` after
  every code change. Tarball script uses bash-4 features; on macOS bash-3 hosts run via `/opt/homebrew/bin/bash`.

---

## 🧠 Key technical anchors (commit references)

- **Coverage gate decision logic**: `features_sports_service/compute/coverage_gate.py` (commits `cf298fa`, `474722c`,
  `fa7464c`) — wraps `FEATURE_UPSTREAM_REQUIREMENTS` + `in_coverage`, returns
  `CoverageVerdict.READY/UPSTREAM_MISSING/OUT_OF_COVERAGE`.
- **Per-feature expected-dates walker**: `_features_sports_expected_dates_for_calculator` in
  `deployment-api/deployment_api/services/data_status_service.py` (commit `6f7771f`) — intersection of required-upstream
  calendars, derived-recursion with cycle detection.
- **Per-feature axis branch**: same file, `_sports_honest_coverage` (commit `51bcc26`) — routes feature_group entries to
  the new axis, filters manifest by `feature_group=<calc_name>`.
- **Coverage report CLI**: `features_sports_service/scripts/honest_coverage_report.py` (commit `25f6d73`) —
  operator-facing pre-backfill audit. Smoke-tested end-to-end.
- **Drift comparator**: `deployment_api/services/coverage_drift.py` (commit `acd2d25`) —
  `detect_drift(prev_snap, cur_snap, threshold_pct=5.0) -> list[DriftEvent]`.

---

## 🚦 Definition of done for this handoff

- All 7 Stage A backfill VMs launched + completed + validated (Phase 4)
- Stage B-D backfills completed (Phase 5-7)
- deployment-ui data-status tab surfaces per-calculator coverage rows (Phase 8.A)
- Daily drift snapshot Cloud Run job + structured event emission live (Phase 8.B remainder)
- Plan flipped to `status: complete` and unlocked from `live-defi-rollout`

When ready, ask the user to confirm before each Stage A backfill VM launch — they'll want to spot-check coverage_report
output + agree on the date window before burning VM hours.
