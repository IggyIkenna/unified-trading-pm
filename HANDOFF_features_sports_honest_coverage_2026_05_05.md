# HANDOFF — features-sports honest-coverage (2026-05-05)

You are picking up the **features-sports honest-coverage** project mid-flight. The previous agent shipped Phase 0
(inventory) and Phase 0.5 (wiring two new calculators) and just appended Phase 0.6 + Phase 0.7 todos to the plan. Your
job is to proceed through Phase 0.6 → 0.7 coordination → Phase 1 → ... → Phase 8.

**Workspace root:** `/Users/ikennaigboaka/Code/unified-trading-system-repos/` **Active branch (every repo):**
`live-defi-rollout` **Plan file:** `unified-trading-pm/plans/active/features_sports_honest_coverage_2026_05_05.plan.md`
**Plan status:** `locked_by: live-defi-rollout` (do NOT unlock without `[unlock-plan]` in the commit message AND user
approval). **Memory file with all context:**
`~/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/project_features_sports_honest_coverage_2026_05_05.md`

---

## ⚠ Read these BEFORE writing any code

1. `unified-trading-system-repos/.claude/CLAUDE.md` — workspace rules (asset_group vocab, manifest v5, honest absence,
   sports GCS path SSOT, source coverage windows, VM tarball, singleton launchers, **no fire-and-forget VM launches**).
2. `unified-trading-system-repos/features-sports-service/.claude/CLAUDE.md` — repo-local rules.
3. `unified-trading-pm/plans/active/features_sports_honest_coverage_2026_05_05.plan.md` — the actual plan.
4. `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — if you spawn sub-agents, paste this at the top of
   their prompt. Sub-agents do NOT inherit rules.

---

## ✅ What's done (DO NOT redo)

### Phase 0 — Inventory (CORRECTED)

- The runtime feature catalog has **1,142 features** (986 derived + 156 odds) across **32 calculators**.
- **Source of truth is `features_sports_service.schemas.feature_catalog.DERIVED_CALCULATOR_GROUPS`**, not the
  `feature_definitions.yaml` (YAML was stale documentation).
- `features-sports-service/scripts/regenerate_feature_definitions.py` exists to rebuild the YAML from the runtime
  catalog (CALC_UPSTREAM dict maps each calculator to its upstream entities + Stage A/C/D).

### Phase 0.5 — Two captured-but-unconsumed sources wired

- **`sfi_progressive_calculator.py`** (31 features) — halftime detection from SFI per-match 30s snapshots.
  - Algorithm: 5 halftime timing fields + `ht_detection_method` + 18 per-half per-team + 7 differentials/odds-drift.
  - Constants: `_HT_LOWER_SECONDS=2280` (38min), `_HT_UPPER_SECONDS=3900` (65min), `_HT_MIN_DURATION=300` (5min),
    `_HT_MAX_DURATION=1500` (25min).
  - Signal 1 — xG-NaN region: if match HAS xG, find longest contiguous NaN run inside [38min, 65min] with [5min, 25min]
    duration.
  - Signal 2 — counter-freeze fallback: when xG isn't available, find longest run where ALL of `attacks_dangerous`,
    `attacks_dangerous_away`, `shots_on_target`, `shots_off_target`, `corners` are frozen.
  - Returns `(ht_start, ht_end, method)` where method ∈ {`xg_nan`, `counter_freeze`, `unavailable`}.
  - **DO NOT** revert to using SFI's static `ht_start_timer` field — it's a constant 2550 across every match (NOT
    per-match); `ht_end_timer` is 100% NULL. The previous agent's bug.
  - Pre-flight validation already done: 27 fixtures sampled — 7 detected (5 xg_nan + 2 counter_freeze), 20 unavailable
    (mostly K-League which has no xG capture).
- **`footystats_predictions_calculator.py`** (27 features) — `fs_*` pass-throughs
  (btts/o25/xg_prematch/ppg/corners/cards/offsides \_potential). Last-write-wins per fixture_id.
- Both wired into `derived_features_exporter._run_new_calculators` as Group 21 + Group 22.
- `gcs_reader.REFERENCE_ENTITY_TYPES` extended with `progressive_stats`.

### Retired entities (do NOT re-add)

`TRANSFERMARKT_LEAGUES` and `SFI_LEAGUES` were retired across UAC + deployment-api + instruments-service + 92,943
manifest rows in earlier session work. They were provider-id config mappings, not captured GCS data. Live in
`unified_api_contracts/canonical/domain/sports/provider_league_ids.py`.

---

## 🚧 Pre-Phase-1 audit tasks (DO BEFORE Phase 1)

### Audit 1: Pull in CosmicTrader recent fixes (BLOCKING)

Operator (Iggy) flagged that another agent (**CosmicTrader**) shipped useful fixes across these 8 repos. Review them
BEFORE Phase 1 implementation and absorb the patterns/changes that affect your work:

```bash
for repo in deployment-service deployment-api unified-trading-system-ui unified-trading-pm \
           unified-api-contracts instruments-service market-tick-data-service \
           market-data-processing-service; do
  echo "=== $repo ==="
  cd "/Users/ikennaigboaka/Code/unified-trading-system-repos/$repo"
  git log --since="2026-04-29" --pretty=format:"%h %ae %s" origin/live-defi-rollout | grep -iE "cosmic|trader" || true
  git log --since="2026-04-29" --pretty=format:"%h %s" origin/live-defi-rollout | head -20
done
```

For each repo, read recent commits (especially anything touching honest-coverage, manifest, sports, features, or
deployment-UI data-status), record which ones affect Phase 1+ in the plan as "Pre-Phase-1 absorbed: <commit-hash>", and
update the plan with any new conventions/rules that emerged.

### Audit 2: Phase 0.7 — odds_api venue→data_source migration coordination (BLOCKING for Stage A odds features)

A separate in-flight agent is migrating odds_api from `venue=odds_api` to `data_source=odds_api` because odds_api is an
aggregator, not a venue. Stage A includes ~7 odds_calculator features that will break if you implement
FEATURE_UPSTREAM_REQUIREMENTS using `venue=odds_api`.

Per Phase 0.7 in the plan:

- P0.7.A — verify the migration is on origin/live-defi-rollout. Check UAC sports facade renames + deployment-api
  SPORTS_DATA_TYPE_META updates + MTDS/instruments-service writer updates + manifest backfill of legacy `venue=odds_api`
  rows.
- P0.7.B — model FEATURE_UPSTREAM_REQUIREMENTS in Phase 1 with `data_source` axis for odds_api, NOT `venue`.
- P0.7.C — verify `candidate_parquet_paths(data_type="ODDS_HORIZON_BUCKET")` in UAC reflects the new schema.
- P0.7.D — sanity-check 92% upstream ODDS coverage hasn't regressed via deployment-UI data-status before declaring Phase
  4.G ready.

If Audit 1 + Audit 2 conflict (e.g. CosmicTrader fixed odds_api differently), check with the user before resolving.

---

## 🎯 Next concrete actionable: Phase 0.6 (standalone SFI progressive backfill VM)

**Goal:** Get halftime features computed for the entire SFI coverage window (2020-01-01 → today) in ~30-45min via one
e2-standard-4 VM, BEFORE Phase 1 starts. That way the rest of the pipeline lights up with halftime already complete.

The 6 todos are in the plan as P0.6.A → P0.6.F. Outline:

1. **P0.6.A** — Create `deployment-service/scripts/vm/launch-sfi-progressive-features-backfill-vm.sh`. Use existing
   sports backfill VM launchers as template (e.g. `launch-sfi-forward-poll.sh` for the singleton-lock pattern).
   Singleton-locked, e2-standard-4, prefix `features-sfi-progressive-`. Add the prefix to
   `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET` in `deployment-service/scripts/vm/vm_zombie_watchdog.py` (heartbeat-only —
   no shard bucket). After dict update, relaunch the watchdog VM (it only fetches the Python at boot).
2. **P0.6.B** — Pick ONE of these two paths:
   - A: Add `--calculator sfi_progressive` filter to features-sports-service CLI (preferred — reusable for other
     calculators in Phase 4-7).
   - B: Write `features-sports-service/scripts/compute_sfi_progressive_only.py` calling `compute_sfi_progressive_batch`
     directly per fixture-day partition (one-off; skip if `--calculator` already exists or you're going with A).
3. **P0.6.C** — Refresh sports tarballs:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`.
4. **P0.6.D** — Launch the VM. **Pair the launch with active event-stream verification** (per the no-fire-and-forget
   rule in `.claude/CLAUDE.md`):
   - Wait 90s, then `gcloud storage ls gs://{pid}-events/events/features-sports-service/{today}/{vm-name}/`.
   - Confirm a `STARTED` event lands.
   - Periodically check progress events; stalled progression == silently broken VM.
   - Confirm `STOPPED` (or `FAILED`) at exit.
5. **P0.6.E** — Validate output: 5 random fixtures across 2020-2026, spot-check 3 xg_nan + 3 counter_freeze + 3
   unavailable. Confirm `ht_start_seconds` ∈ [38min, 65min] and `ht_duration_seconds` ∈ [5min, 25min] for detected
   cases.
6. **P0.6.F** — Detection-rate summary into the plan: % xg_nan / % counter_freeze / % unavailable per league_id. Helps
   Phase 1 set realistic FEATURE_UPSTREAM_REQUIREMENTS for halftime features (e.g. flag K-League halftime features as
   "ht_unavailable expected").

---

## 📋 Subsequent phases (after 0.6)

- **Phase 1** — UAC additions: `UpstreamReq` dataclass, `FEATURE_UPSTREAM_REQUIREMENTS` dict,
  `in_coverage(source, data_type, league_id, date)` helper. SSOT for which feature needs which upstream rows.
- **Phase 2** — features-sports-service compute logic: distinguish NaN-expected (in_coverage but row missing →
  NaN-empty-confirmed) vs upstream-missing (out-of-coverage → skip).
- **Phase 3** — deployment-api per-feature axis calc.
- **Phase 4** — Stage A backfill (single-source: footystats → odds_api → transfermarkt → SFI → api_football).
- **Phase 5** — Stage B per-source.
- **Phase 6** — Stage C cross-source joins.
- **Phase 7** — Stage D enriched/derived.
- **Phase 8** — UI + drift monitoring.

---

## 🛠 Workspace conventions (CRITICAL)

- `cd <repo> && bash scripts/quality-gates.sh` for tests (uses repo `.venv`). NEVER `pytest` directly.
- `bash scripts/quickmerge.sh "msg" --agent --files <file1> <file2>` for commits + push (NOT `git push`).
- Conventional commit prefixes required: `feat(scope):` / `fix(scope):` / `docs(scope):` / `chore(scope):`.
- `uv pip install -e .` (NOT `pip install`, NOT `.[dev]`).
- `basedpyright` (not `pyright`); always run with `run_timeout 120 basedpyright <source_dir>/`.
- No `os.getenv()` — use `UnifiedCloudConfig`.
- No `try/except ImportError` around library imports — fail loud.
- No `# type: ignore` — fix the root cause.
- **Honest absence vs fake placeholders** — re-read the workspace CLAUDE.md section on this. Three categories:
  expected-upstream-gap (`record_empty`), unexpected-upstream-pipeline-gap (`DependencyError fail_fast`),
  reader/schema-drift bug (raise loud).
- **Sports GCS path SSOT** — never hardcode `sports_reference/by_date/...`. Use
  `from unified_api_contracts.sports import candidate_parquet_paths, candidate_parquet_uris, SPORTS_DATA_TYPE_TO_FOLDER, SPORTS_DATA_TYPE_LAYOUT`.
- **Source coverage windows** — `SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS` in UAC
  `unified_api_contracts.sports`. Pass `data_type=` through `clip_dates_to_source_coverage` /
  `get_source_coverage_start` for per-(source, data_type) overrides.
- **VM naming**: every `gcloud compute instances create <NAME>` first segment must be a prefix in `VM_PREFIX_TO_BUCKET`
  in `deployment-service/scripts/vm/vm_zombie_watchdog.py`. Adding a new prefix without updating the dict makes the VM
  invisible to the zombie watchdog → unbounded burn.
- **VM tarball deployment**: refresh tarballs after every code change with
  `bash deployment-service/scripts/vm/create-code-tarballs.sh <flag>` (`--asset-group SPORTS` for sports work).
  Forgetting silently runs stale code.
- `feature_catalog.py` is the runtime SSOT, NOT the YAML.

---

## 🧠 Key technical anchors

- **Halftime detection** — see
  `features-sports-service/features_sports_service/calculators/sfi_progressive_calculator.py` for the exact algorithm.
  Don't change without re-validating against ≥27 real fixtures across at least 3 leagues.
- **Footystats predictions** — see same dir's `footystats_predictions_calculator.py`. 27 pass-through `fs_*` features.
  Latest-fetched_at-hour wins per fixture.
- **Manifest v5** — `record_empty(row_key=..., attempted_at=...)` for legitimately-zero-rows;
  `record_failed(row_key=..., error=classify_venue_error(exc), attempted_at=...)` for exceptions. Never overload `venue`
  with non-venue data.
- **per_league_periodic vs per_league_per_fixture_date axes** — already wired in deployment-api `data_status_service.py`
  per the previous session's bucket-match algorithm. PLAYER_VALUES + TRANSFERMARKT_LEAGUES cadence is `90` (quarterly
  trigger), not `7` (weekly).

---

## 🚦 Definition of done for this handoff

- Audit 1 (CosmicTrader fixes) complete — plan updated with absorbed commits.
- Phase 0.7 (odds_api migration) coordinated — verified the migration landed before starting Phase 1.
- Phase 0.6 (SFI progressive backfill VM) shipped: VM launched, validated, detection-rate stats in plan.
- Phase 1 (UAC additions) ready to start with FEATURE_UPSTREAM_REQUIREMENTS using the post-migration `data_source` axis
  for odds_api.

When ready, ask the user to confirm before progressing past Phase 0.6 — they may want to spot-check the halftime output
first.
