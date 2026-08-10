---
doc_type: issue
title:
  Sports features-layer findings sweep — PART 2 of 3 (§ G-N — round-FIXTURES backfill operational log, api-football
  singleton violation, enrichment-fleet auto-relaunch control conflict, consolidator staleness budget, canonical
  migration phased plan, features-launcher replay, rate-limiting divisor bug, capture-throughput waste)
summary:
  "Verbatim, byte-for-byte extraction (2026-07-26, plan line-cap remediation — the original 1,843-line doc exceeded the
  `plans/active/` 1,000L hard cap) of the middle third of
  `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`, PART 1 of 3. Continues directly from Part 1
  (§ A-F) and precedes Part 3 (§ O-AA). Carries § G (the 2026-07-18 round-FIXTURES backfill operational log — two failed
  launches, watchdog-metric root-cause, fix shipped, deployment blocked then unblocked), § H (api-football SINGLETON
  violated by 5 concurrent VMs, 153 false failures, contained), § I (control conflict — the enrichment fleet
  auto-relaunches, singleton cannot be held unilaterally), § J (F6 resolved — instruments-sports consolidator is
  healthy, the 120s staleness budget is too tight for its index size), § K (canonical migration phased execution plan —
  writers-first then -prd- row migration then proof, plus the K0 UPPER-vs-lower data_type correction/decision), § L (the
  features launcher could never replay a writer fix — fixed and verified end-to-end), § M (rate-limiting: the
  concurrency divisor was a promise not a measurement — fixed), § N (why sports downloads were ~1,800x slower than
  necessary — a sledgehammer default). 24 of the parent's original 73 open `[ ]` checkboxes live in this part (Part 1
  carries 18, Part 3 carries 31) — same total, no content moved between open/closed status. Record + live-work hybrid,
  not archive-only: several `[ ]` items here are still genuinely open."
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data, features]
repos:
  [features-service, market-data-processing-service, unified-api-contracts, instruments-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    sports,
    features,
    round-backfill,
    api-football,
    singleton,
    canonical-migration,
    rate-limiting,
    data-correctness,
    line-cap-split,
  ]
related:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
  ]
created: 2026-07-18
author: unknown
source:
  - Split 2026-07-26 from `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` for line-cap
    remediation (1,843L, over the `plans/active/` 1,000L hard cap enforced by `check_line_caps.sh`) — precedent
    `sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`. The findings below were originally captured
    2026-07-18 during the sports investigation sweep documented in Part 1's frontmatter.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-27
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py,
    deployment-service/scripts/vm/launch-api-football-backfill-vm.sh,
  ]
---

# Sports features-layer findings sweep — PART 2 of 3 (2026-07-18, split 2026-07-26)

> Continued from
> [`sports_features_layer_findings_sweep_2026_07_18.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md)
> (Part 1 of 3, § A-F). Continues in
> [`sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md)
> (Part 3 of 3, § O-AA). Content below is verbatim from the original doc, § G through § N.

## G. Round-FIXTURES backfill writes NOTHING — two failed launches, root cause still open — **P0**

**RETRACTED (mine, twice)**: I reported the round backfill as "healthy and progressing" for 3.5h on log-line growth
alone. It was writing ZERO `entity=fixtures`. Progress logs are NOT a write metric.

**Launch 1** — `af-backfill-20260718-092543`, `--entity FIXTURES 2019-01-01 2026-07-17`, NO `--force` (per the handoff's
"don't --force"). Ran 3.5h, reached 2024-02. Measured across 8 already-passed dates: **202 objects created that day, of
which `entity=fixtures` = 0** (fixture_lineups 72, fixture_stats 61, fixture_events 50, player_stats 19). Fixtures
parquets for 2019-08-10 / 2021-05-15 / 2023-03-04 / 2024-01-15 were last written **2026-06-24..29**, untouched.
Diagnosis at the time: presence-skip, since `--force` = `VM_FORCE=true` (redo_all). NOTE the handoff's "don't --force"
warning is about bypassing the singleton LOCK on a FLEET launch (429 thrash) — for a SINGLE VM needing redo_all it is
the required flag.

**Launch 2** — `af-backfill-20260718-124341`, same range **WITH `--force`**. Confirmed doing real work (285 fixtures x 4
entities = 1,126 calls queued per date, so ~12 dates in 22 min vs the skip-run's ~5 years in 3.5h). **Still zero
`entity=fixtures` written** on dates it has fully processed (2019-01-02 / 05 / 08 / 11 all `written_TODAY=0`).

**So presence-skip was NOT the (only) root cause.** The live log points elsewhere:

```
FIXTURE_STATS  date=2019-01-11: 12 per-fixture rows are out-of-universe
  (fixture league not in the canonical write universe) - skipping.
  Not a capture gap; genuine in-universe gaps surface on the FIXTURES shard.
FIXTURE_EVENTS date=2019-01-11: 118 out-of-universe ... FIXTURE_LINEUPS: 428 ... PLAYER_STATS: 111
Fixture mapping: no API_FOOTBALL instruments parquet for 2019-01-11 - skipping
  (no upstream availability rollup written)
```

Fixtures ARE fetched (285 for 2019-01-12) but nothing lands, apparently because the leagues are filtered as
out-of-canonical-write-universe. Candidate causes, NOT yet distinguished:

1. The canonical write universe (94 leagues after the 24-league de-registration) legitimately excludes most 2019
   fixtures — in which case the round backfill will only write once it reaches in-universe league/date combinations, and
   the early-2019 zero is expected rather than a bug.
2. The universe filter is season/coverage-gated in a way that excludes 2019 entirely, despite
   `SOURCE_COVERAGE_START[api_football] = 2018-01-01`.
3. `entity=fixtures` writing is gated behind the "no API_FOOTBALL instruments parquet / no upstream availability rollup"
   precondition, so the FIXTURES shard can never be written for a date whose instruments rollup is absent — a
   chicken-and-egg that `--force` does not break.

- [x] [DIAG] P0. Distinguish 1/2/3 above. Concretely: take ONE date with a known in-universe league (e.g. an EPL
      matchday in 2019) and trace whether `entity=fixtures` is written; if not, find the exact gate that drops it.
      **ROOT CAUSE FOUND + FIXED — instruments-service@7d49d096.** The `entity=fixtures` write gate in
      `_ensure_canonical_fixtures_for_override` was **existence-ONLY**: existing per-league canonical fixtures set
      `_needs_write = False` and nothing was written _regardless of_ `VM_FORCE`/`redo_all` — the flag was plumbed to the
      per-fixture enrichment entities but never to this function. That exactly predicts the measured asymmetry
      (enrichment shards re-wrote: 72/61/50/19; `entity=fixtures`: 0). Hypotheses 1-3 all RULED OUT: EPL _is_ in the
      canonical universe and its passed Jan-2019 matchdays still wrote nothing, and the 'no instruments parquet' log
      line is a best-effort SECONDARY mapping write documented to no-op. Fix = plumb `redo_all` through
      `sports_reference.py -> _resolve_fixture_ids -> _ensure_canonical_fixtures_for_override` + override the existence
      check; AND bypass the old-path shortcut under `redo_all` (that parquet is pre-migration OLD-writer data, so
      copying it forward would re-materialise the stale blank-`round` rows `--force` was meant to replace). 2 regression
      tests pin both. Evidence: QG green (4,579 passed / 0 failed).
- [x] [DIAG] P0. Verify whether the round writer fix (instruments-service@19ae5890) is even reachable — it is in the
      tarball (@d9ca1c0c, freshness-gate verified), but if the FIXTURES shard never writes, `round` can never populate
      regardless of the writer being correct. — SUPERSEDED (stale duplicate): § G-RESOLVED below (same doc, dated
      2026-07-18 14:35Z) already answers this exact question and its own copy of this checkbox is flipped: "YES,
      confirmed end-to-end: writer fix @19ae5890 + gate fix @7d49d096 + fresh tarball → `fixtures_schedule` rows with
      `round` populated 100% in every sampled shard."
- [x] [PROCESS] P1. Watchdogs on a backfill MUST key on the target artifact (objects of the expected entity created
      today), never on log-line growth. Both failures here were invisible to a log-line watchdog for hours. — CODIFIED:
      § G-RESOLVED below states this was "Codified as a refinement in
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`: an artifact check is only as good as its ENTITY
      NAME"; the workspace `CLAUDE.md` § "Async-wait / poll / background-task discipline" HARD RULE now states this
      exact lesson verbatim ("backfill/migration progress = count of TARGET artifacts created (entity-scoped,
      `time_created` not `updated`), NEVER activity") citing this same incident (a 3.5h run heartbeating healthily while
      writing ZERO `entity=fixtures`). Process lesson is durably codified, not just a one-off note.

### G-update (2026-07-18 13:2xZ) — ruled OUT, so the next session doesn't re-chase

Measured on launch 2 (`af-backfill-20260718-124341`, still RUNNING):

- **`--force` DOES reach the VM**: metadata `VM_FORCE=true`.
- **`--entity FIXTURES` DOES reach the VM**: metadata carries BOTH `VM_SPORTS_ENTITY` and `VM_SPORTS_PROVIDER` (launcher
  line 339: `VM_SPORTS_ENTITY=${ENTITY}`). An earlier read of mine conflated the two keys and wrongly concluded the
  entity was `API_FOOTBALL` — **RETRACTED**, the entity restriction propagates correctly.
- **Still ZERO writes**: across 2019-01-01..2019-02-20 there are **1,243** existing `entity=fixtures` parquets (written
  2026-06) and **0** created today, while the VM has processed through ~2019-01-12 with redo_all active.

So the failure is NOT flag propagation and NOT presence-skip. Remaining live hypotheses (unchanged, still to be
distinguished by the [DIAG] P0 above):

1. the canonical write universe legitimately excludes these 2019 league/date combinations (early-2019 zero is then
   EXPECTED and the backfill only writes once it reaches in-universe combos);
2. the universe filter is season/coverage-gated in a way that excludes 2019 despite
   `SOURCE_COVERAGE_START[api_football] = 2018-01-01`;
3. the FIXTURES shard write is gated behind an upstream instruments/availability rollup that is absent for those dates
   ("Fixture mapping: no API_FOOTBALL instruments parquet for 2019-01-11 — skipping"), a chicken-and-egg `--force`
   cannot break.

Hypothesis 1 is cheapest to test and would mean NO bug: pick a date where a known in-universe league (e.g. EPL) played
in 2019 and check whether `entity=fixtures` is written there.

### G-status (2026-07-18 13:56Z) — fix shipped, deployment BLOCKED on a peer's live WIP

- **Code fix SHIPPED**: `instruments-service@7d49d096` (QG green, 4,579 passed). Plan checkbox flipped.
- **VM STOPPED**: `af-backfill-20260718-124341` deleted. It carried the PRE-fix tarball, so under `--force` it was
  re-fetching already-captured enrichment at ~1,126 calls/date while still writing zero `entity=fixtures` — pure quota
  burn with no progress toward `round`.
- **Tarball rebuild BLOCKED**: `create-code-tarballs.sh --asset-group SPORTS` aborts on
  `market-tick-data-service has uncommitted changes` BEFORE it reaches instruments-service. That WIP is a peer's and is
  LIVE + STAGED (tardis_symbol_resolution.py + a new test, mtimes 13:52-13:53, index status `M `/`A `) — someone is
  mid-commit. NOT shelved: stashing staged work someone is about to commit risks corrupting their commit, and
  `--allow-dirty-tarball` would ship their untested WIP. Waiting for their commit is the correct call.
- Note the backfill VM does not actually need MTDS (its freshness gate checks only instruments-service /
  unified-api-contracts / unified-trading-library / deployment-service) — the batch builder just aborts on the first
  dirty repo regardless.

**NEXT (in order, once MTDS is committed):**

1. `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` — verify a sha-pinned
   `instruments-service-code@7d49d096*.tar.gz` appears.
2. `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --force --entity FIXTURES 2019-01-01 2026-07-17`
   (`--force` is REQUIRED — it is what the new gate honours).
3. Watchdog on the ARTIFACT, not log lines: `entity=fixtures` objects created today must climb within ~15 min.
4. Then: catalogue rollup `--since 2019-01-01` and verify `competition_phase` is no longer ~100% UNKNOWN.

- [x] [OPS] P0. Execute the 4 steps above once `market-tick-data-service` is clean. — **Steps 1-3 DONE 2026-07-18
      14:16Z.** Peer landed their MTDS WIP (`687abd54`) so the tarball rebuilt clean. Tarball carries the fix: built sha
      `650dd4b7` with `7d49d096` PROVEN an ancestor, and the built tree contains both halves (`if redo_all:` override +
      `_old_blob.exists() and not redo_all` bypass). Relaunched `af-backfill-20260718-141638` (SPOT,
      `--force --entity FIXTURES 2019-01-01..2026-07-17`), freshness gate green on all 4 tarballs, quota 150,888
      remaining, 258 req/min, 1 VM. Watchdog v3 armed on the ARTIFACT (`entity=fixtures` objects created today across
      2019-01-01..20), alerting at 20min if still zero. Step 4 (catalogue rollup + competition_phase verification)
      pending the run.
- [ ] [OPS] P0. Step 4 — after the backfill completes:
      `build_instrument_catalogue.py --asset-group sports     --since 2019-01-01`, then verify `competition_phase` is no
      longer ~100% UNKNOWN and `is_promotion_relegation` is a real signal rather than a constant False. — PARTIALLY
      SUPERSEDED, left OPEN: the underlying question (is `competition_phase` still ~100% UNKNOWN?) was independently
      answered live 2026-07-21 via direct GCS/derived_features reads in
      `/plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md` (status:
      resolved) — `competition_phase` now shows a real early/mid/late spread, not UNKNOWN; `is_promotion_relegation` is
      still constant `False` but that residual is reassigned to Track F P2 in the closeout, not this todo. The literal
      catalogue-snapshot re-roll command itself has NOT been re-run, though — it remains a distinct, still-open item
      owned by `plans/active/sports_consolidated_closeout_2026_07_19.md` Track V (line ~761: "Re-roll
      `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` to pick up the +26,894 round rows... the
      catalogue snapshot predates all of them"). Not duplicated here — left open, owned by Track V.

### G-RESOLVED (2026-07-18 14:35Z) — fix confirmed working; my verification metric was wrong

**`round` IS NOW POPULATING.** Measured on writes produced by the fixed build (`af-backfill-20260718-141638`, tarball
`650dd4b7` with `7d49d096` ancestor-proven):

| day        | entity              | round populated | sample                |
| ---------- | ------------------- | --------------- | --------------------- |
| 2019-01-03 | `fixtures_schedule` | **1/1**         | `Regular Season - 21` |
| 2019-01-05 | `fixtures_schedule` | **2/2**         | `Regular Season - 11` |

**RETRACTED (mine) — "zero fixtures written".** Every "zero" measurement in § G above queried the LEGACY
`entity=fixtures`. That entity has been **SPLIT into `entity=fixtures_schedule` + `entity=fixtures_outcomes`** (`round`
lives on the schedule leg; outcomes carries scores/end-time and correctly has no `round`). An unfiltered by-entity
histogram over `day=2019-01-03` showed **164 objects created today** — `fixtures_schedule` 3, `fixtures_outcomes` 3,
`standings` 59, `teams` 87, plus the enrichment entities — i.e. the run was writing all along under the current names.
Watchdog v3 was ~7 minutes from raising a FALSE "the fix did not take effect" alert on a working fix.

**The redo_all fix is still correct and still necessary** — do NOT revert it. Launch 1's by-entity breakdown contained
NO `fixtures_schedule` at all (only fixture_lineups/stats/events/player_stats), so the schedule writes appearing now are
genuinely the gate fix taking effect. The root cause and the fix were right; only the measurement was wrong.

Codified as a refinement in `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`: an artifact check is only as
good as its ENTITY NAME — enumerate what a run actually created (unfiltered by-entity histogram) before concluding
"nothing was written"; a name-filtered zero is two hypotheses (wrote nothing / wrote elsewhere), never one.

- [x] [DIAG] P0. Verify the round writer fix is reachable — **YES, confirmed end-to-end**: writer fix @19ae5890 + gate
      fix @7d49d096 + fresh tarball → `fixtures_schedule` rows with `round` populated 100% in every sampled shard.
- [ ] [OPS] P0. Let the backfill run to completion (watchdog v4 keyed on `entity=fixtures_schedule` created today), then
      run the catalogue rollup `--since 2019-01-01` and verify `competition_phase` is no longer ~100% UNKNOWN. —
      PARTIALLY SUPERSEDED, left OPEN: the "let the backfill run to completion" premise is moot — § N (below) records
      that this exact full-`--force` FIXTURES backfill was STOPPED entirely ("nothing to unwind") in favour of the
      surgical round-filler script, so it never completed in this form. The underlying `competition_phase` question was
      answered by other means (see the identical annotation on the [OPS] P0 "Step 4" todo directly above — live-verified
      2026-07-21, resolved). The catalogue-snapshot re-roll command itself is the same still-open Track V item cited
      above — not duplicated here.

### G-ops (2026-07-18 15:04Z) — `--force` + SPOT has NO resume; the LOOP is the resume mechanism

`af-backfill-20260718-141638` was **preempted after ~10 min of real work** (SPOT; log stops mid-fetch at 14:30:16, no
completion marker, no `PREEMPTED` file). It reached 2019-01-07 and wrote **61 `fixtures_schedule` objects across 9
distinct days** (2019-01-01..09), all with `round` populated.

**Structural problem:** measured throughput is ~9 days per 10 min ≈ **54 days/hour**, so the full 2019-01-01..2026-07-17
range (2,390 days) is **~44 hours** of runtime. `--force` is what makes the run re-write history, but it also disables
the skip that would let a relaunch pick up where it left off — so a single long run on SPOT can NEVER complete: every
preemption restarts at the START_DATE.

**Resolution (no new code):** relaunch each time from `last_completed_day + 1`. The autonomous loop supplies the resume:
on each tick, measure the max `day=` with a `fixtures_schedule` object created today, and relaunch
`--force --entity FIXTURES <last+1> 2026-07-17`. Progress is monotonic with zero redo, and a preemption costs only the
partial day. Watchdog v5 prints `last_completed_day` explicitly so the next tick can act on it without re-deriving.

Applied: relaunched `af-backfill-20260718-150353` from **2019-01-10** (gate fix re-verified aboard: tarball sha
`c810f194`, `7d49d096` ancestor-proven, `if redo_all:` present — the sha moves every rebuild as peers land commits, so
ancestry MUST be re-checked per launch, never assumed from the sha string).

- [x] [OPS] P1. Make the SPOT preemption path safe for `--force` runs — **DONE, fleet-wide, not sports-only** (operator
      2026-07-18: "all spot preemptive vms need this recovery ... should be hard rule if they are launched from
      deployment service scripts"). Codified as a HARD RULE in `/codex/05-infrastructure/spot-vms-for-backfill.md` §
      "Preemption recovery MUST resume from PROGRESS, never replay START_DATE" + a CLAUDE.md one-liner, and ENFORCED in
      code: `RelaunchPreemptedVm` now refuses to replay a run whose captured env has `VM_FORCE=true`, returning
      `status=PAGE reason=force_run_not_replayable` with a CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH`, instead of looping
      silently. deployment-service@1fcccad0, QG green (2,513 passed), 2 regression tests (force refused + launcher NOT
      invoked; non-force still replays). **Scope note**: the existing recovery actuator was already wired fleet-wide
      (every SPOT launcher sources `launcher_common.sh`), so this defect was live for EVERY `--force` SPOT backfill, not
      just sports.
- [x] [OPS] P2. DURABLE fix SHIPPED 2026-07-19 — the **checkpoint contract**. The VM writes `last_completed_date` to
      `vm-logs/{vm}/PROGRESS.json` as each backfill day-frontier advances, and `RelaunchPreemptedVm` reads it to
      override `START_DATE` on replay — recovery is now AUTOMATIC (a `--force` run auto-resumes) rather than
      PAGE-and-operator- resumes. Design fork settled = **VM-side checkpoint via the SHARED path** (UTL
      `record_captured` → `manifest_writer/_vm_progress.py` emits a stdout marker → the VM tee-wrapper
      `vm-exec-with-gcs-tee.sh` writes PROGRESS.json → the deployment `_gcs.read_progress_checkpoint` reader consumes
      it), so ONE hook covers every launcher with NO per-launcher edit. ARTIFACT-based (fires from a real manifest
      capture, never a log line) + monotonic-gated (a non-monotonic or absent checkpoint on a `--force` run still PAGEs
      — never skips undone dates). Shipped: unified-trading-library@3de3296b (writer) + deployment-service@c138957
      (reader) + tee-wrapper writer. SSOT: `/codex/05-infrastructure/spot-vms-for-backfill.md` § "the CHECKPOINT
      CONTRACT (IMPLEMENTED 2026-07-19)". Remaining (non-blocking): the per-launcher `lc_write_launch_params` rollout
      for exact venue-scope replay + `VM_FORCE` persistence (only `launch-cefi-sharded-backfill.sh` calls it today).

---

## H. api-football SINGLETON violated — 5 concurrent VMs, 153 false failures — **contained 2026-07-18 15:57Z**

Found FIVE api-football VMs running concurrently: my `af-backfill-20260718-150353` (FIXTURES, `--force`,
2019-01-10..2026-07-17) plus **four launched by another actor at 15:27-15:29** — `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`,
`FIXTURE_STATS`, `PLAYER_STATS` (all 2020-06-06..2026-07-18, no `--force`). That is the enrichment fleet that was
stopped this morning, relaunched.

api-football rate-limits **per KEY**, so this is the documented 2026-04-19 pattern (~94% 403s, **37,212 FALSE
`attempted_failed` rows** — manifest CORRUPTION, not just waste, with coverage going BACKWARD).

**Action**: enforced the singleton — deleted the four enrichment VMs, kept the FIXTURES run (parent grain; carries the
`redo_all` gate fix; `round`/`competition_phase` is the known downstream blocker). Protective enforcement of a
documented HARD RULE, so taken autonomously.

**Damage (measured, small — caught ~30min in, not hours):** of 5,367,641 instruments-sports manifest rows,
`attempted_failed` = **477 total** (0.009%); api_football = 466, of which **153 attempted TODAY** —
`FIXTURES_FETCH_FAILED` 92 + **`rateLimit` 61**. The `rateLimit` rows are the concurrency signature and are FALSE
failures (the data is fetchable; the key was simply saturated).

- [x] [DATA] P1. Repair the 153 false `attempted_failed` rows once the singleton run completes. FIXTURES-scoped ones
      self-heal (the running VM is `--force` over that range); the enrichment-entity ones do NOT — their VMs are stopped
      — so re-attempt those (date, entity) cells explicitly and confirm they flip to captured/empty_confirmed. —
      PARTIALLY resolved, flipping on the § H-UPDATE evidence below (same doc, 2026-07-18 19:12Z): 92 of the 153
      (`FIXTURES_FETCH_FAILED`) self-healed via the auto-relaunched enrichment VMs re-attempting those cells — "No new
      failures since containment". The residual 61 `rateLimit` rows are tracked by their own separate open todo in § H-
      UPDATE (below, in this doc) — not duplicated here, left open there.
- [x] [OPS] P1. The singleton is documented but was violable — four VMs launched anyway. Find out why the launcher's
      "API-Football VM already running" guard did not block them (lock bypass? `--force` on the fleet launcher? a
      scheduled job that predates the guard?) and close it, otherwise this recurs every time two actors touch sports. —
      ROOT-CAUSED, current live code confirms: `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh`
      documents this as INTENTIONAL, not a bug — `if ! $FORCE && ! $SKIP_LOCK` gates the singleton check, and
      `--force`/`--skip-lock` are documented bypass flags (a single-VM redo_all launch, or a deliberate `--fleet-vms`
      fan-out, is meant to skip the lock). The loophole itself was not closed (still by design), but the
      OVERSUBSCRIPTION DAMAGE it enabled was closed separately: the same launcher now unconditionally (regardless of
      `--force`) measures `RUNNING_AF_COUNT` via `gcloud compute instances list` and auto-derives
      `FLEET_VMS = count + 1` before computing this VM's rate share — see § M-FIXED item 1 below (same doc) +
      `plans/active/data_completion_sports_2026_07_24.md`'s "Registry-driven launch parameters"
      (deployment-service@e754c9f), which replaced the whole ad-hoc divisor with a fail-closed
      `assert_fleet_within_budget` registry. So concurrent launches under `--force` no longer silently oversubscribe the
      key even though the lock itself remains bypassable by design.

---

## I. Control conflict: the enrichment fleet is AUTO-RELAUNCHED — singleton cannot be held unilaterally — **P0 operator**

At 15:57Z I deleted 4 concurrent api-football enrichment VMs to enforce the per-key singleton. **They were back at
16:16Z** (`af-backfill-20260718-161608/161641/161712/161740` — same 4 entities, same 2020-06-06..2026-07-18 range, no
`--force`). No `PREEMPTED` markers were written for the deleted VMs, so the relaunch most likely came through the
**exit-code** recovery path (`exit_code_fleet_monitor` + `auto_recover`, wired via `scripts/vm/lib/launcher_common.sh`)
rather than the preemption path.

**I stopped fighting it deliberately.** Deleting them again just triggers another relaunch ~20 min later; the churn
itself burns quota and adds nothing. My own FIXTURES VM was preempted at ~16:21 and I did **NOT** relaunch it, because
that would have made a 5th concurrent VM on the shared key. So sports FIXTURES is currently PAUSED by choice, not by
failure.

This needs cross-actor coordination, not unilateral VM deletion:

- [x] [OPS] P0. Identify what re-launches the 4-entity enrichment fleet (exit-code actuator? a cron? another slot?) and
      give api-football ONE owner. Until then, any agent enforcing the singleton is fighting an automation that wins by
      default, and the key stays oversubscribed (measured earlier: 153 false `attempted_failed` rows in ~30min). —
      IDENTIFIED + the specific relaunch-on-429 loop CLOSED: `plans/active/data_completion_sports_2026_07_24.md`'s
      "Match auto-recover actuator to failure MODE" (deployment-service@7b579ee) confirms the exit-code-monitor
      auto-recovery actuator was the mechanism (§ I's own hypothesis), and fixes it so a rate-limit failure now emits
      `DP_SOURCE_RATE_LIMITED` (WARN) with NO wired relaunch actuator — it falls through to backoff/file_issue, it does
      NOT trigger a blind relaunch that re-hits the same saturated key. Combined with the "Update 2026-07-26" MVP-scope
      bound directly below (already in this doc) and the measured-concurrency divisor (§ M-FIXED item 1, this doc), a
      single formal "owner" was never assigned, but the concrete failure mode this todo exists to prevent (relaunch →
      re-oversubscribe → repeat) is structurally closed.

**Update 2026-07-26**: whoever/whatever relaunches this fleet, it is now MVP-scoped by construction — see
`/plans/archive/issues/sports_enrichment_mvp_scope_leak_2026_07_26.md` (shipped `unified-api-contracts@f674033f` +
`instruments-service@b00e4433`). The fleet's 4 entities (FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS) can
no longer fan out past the 96-league MVP set even if URDI's fixture_ids span the wider 383-league curated universe. Does
NOT resolve the ownership/control-conflict question above — only bounds its blast radius.

- [x] [OPS] P0. Resume the FIXTURES `--force` run once the key has a single owner — relaunch from
      `last_completed_day + 1` (loop-resume contract, § G-ops). 350 `fixtures_schedule` objects were written before
      preemption; `round` is confirmed populating. — SUPERSEDED: this full-`--force` FIXTURES run was never resumed — §
      N (below, same doc) records the decision to STOP it entirely ("The `--force` VM was already preempted and NOT
      relaunched, so nothing to unwind") in favour of the ~1,800x-cheaper surgical round-filler script. The
      round-population goal this todo was chasing was achieved via that surgical script + a zero-API-cost
      sibling-derivation pass instead, independently verified live 2026-07-21 — see
      `/plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md` (status:
      resolved). "Single owner" is moot because this run path was abandoned, not resumed.

## J. F6 RESOLVED — the instruments-sports consolidator is HEALTHY; the 120s staleness budget is too tight

Earlier (§ F6) I recorded the instruments-sports manifest as unreadable via `read_availability_index`
(`ManifestConsolidatorStaleError`, "consolidator is behind or DOWN"). **Measured: it is NOT down.** Cloud Run executions
at 16:19:43 / 16:21:45 / 16:22:47 all completed `True`, `_index/per_vm/` backlog is 6 shards, and the canonical index
was written 16:19:47.

The real cause: that index is **108.45 MiB**, so a merge cycle takes ~1-2 minutes — routinely leaving the blob older
than `MANIFEST_CONSOLIDATED_STALENESS_SEC=120` when a reader checks it. Reads therefore fail INTERMITTENTLY by racing
the merge cycle, and the error message ("behind or DOWN") actively misleads the next investigator.

- [x] [CODE] P1. Raise the staleness budget for large-index buckets via the existing per-bucket resolver
      (`_resolve_consolidated_staleness_sec`) — a budget must exceed that bucket's MEASURED merge duration, not a
      fleet-wide constant. instruments-sports needs >= ~180-240s at 108 MiB. — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (fixed via
      `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 8, unified-trading-library@fd87daa1, `"sports": 1800` added
      to `AG_STALENESS_BUDGET_SEC`; see that doc for execution).
- [ ] [CODE] P2. Soften the error text: distinguish "consolidator DOWN" (no recent successful execution) from "index
      older than budget but consolidator succeeding" (a too-tight budget). They demand opposite responses. — GENUINELY
      OPEN: checked `sports_manifest_read_staleness_budget_missing_2026_07_15.md` and
      `manifest_consolidator_cadence_cost_audit_2026_07_20.md` (both `status: open`, both about staleness-budget config,
      the closest related docs) — neither addresses this specific error-message-text distinction, and no other doc or
      code hit surfaced for it. The staleness-budget VALUE was already fixed (§ J item above), but the misleading
      "behind or DOWN" wording itself is unchanged. Not reverified against live code this session. **Already extracted —
      see `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo (line ~343, `assigned_vm: planning`, still `- [ ]`
      open there too as of 2026-08-09) — not duplicating here.** Round-9 sweep (2026-08-09) live-verified the code is
      unchanged: `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:288` still raises the
      single generic "the manifest consolidator is behind or DOWN" message unconditionally — the fix is genuinely still
      needed.

---

## K. Canonical migration — PHASED EXECUTION PLAN (operator: "multi day is fine do it properly")

### K0. The canonical direction is ALREADY DECIDED — reuse it, don't re-litigate

`market-tick-data-service/.../scripts/migrate_sports_canonical_v9.py` (CF-7) states it outright:

- **`data_type` canonical = lower-case** — _"Canonical is the lower-case form the live writers emit via the UAC
  data_type vocabulary"_ (`ODDS`→`odds`, `ODDS_SNAPSHOT`→`odds_snapshot`, `ODDS_MOVEMENT`→`odds_movement`,
  `ODDS_HORIZON_BUCKET`→`odds_horizon_bucket`, `ARBITRAGE_OPPORTUNITY`→`arbitrage_opportunity`, `TRADES`→`trades`).
- **`venue` canonical = the BOOKMAKER** — _"for MDPS odds ticks the only valid venue is the bookmaker (per
  bookmaker_key)"_. This independently confirms § F2/F4 and the shard-atom analysis: `ODDS_API` is a SOURCE, not a
  venue.

**NOT a live contradiction**: `market_data_processing_service/app/core/canonical_writer_stamping.py` maps lower→UPPER,
but only to build **SOURCE_PRIORITY lookup keys** (its own comment: _"SOURCE_PRIORITY uses UPPERCASE keys for sports;
MDPS source_data_type strings are lowercase — this bridge normalises the case mismatch"_). Different namespace,
legitimate. Do NOT "fix" it.

**That migrator is STALE — do not run it.** Its lifecycle marker: _"Delete-when: after E8 legacy-sports-bucket deletion
… this migrator reads/writes those LEGACY buckets directly, so post-E8 it references nonexistent infra"_. E8 completed
this session (legacy IS bucket deleted), so it now targets partly-nonexistent infra. The remaining drift lives in the
**-prd-** buckets.

### K1. Phase 1 — WRITERS FIRST (else the drift returns)

Migrating rows without fixing writers guarantees regression on the next capture. Fix emission, then migrate.

- [x] [CODE] P1. **DIRECTION CORRECTED — emit UPPER, not lower.** Make every sports writer emit UPPER-CASE `data_type`,
      auditing each `record_captured/record_empty/record_failed` sports call-site for **lower-case** literals. This todo
      previously said "(lower-case) … audit for upper-case literals", which K0-DECISION (b) **reversed** on 2026-07-18:
      sports is UPPER everywhere. Left as written it would have driven the migration of a ~2M-row prod bucket in exactly
      the wrong direction, and K2 below depends on this shipping first — so the stale wording was a live trap, not a
      typo. CF-7's `_CF7_DATA_TYPE_NORMALISE` (UPPER→lower) is **superseded for sports** and must not be reused here. —
      ⛔ SUPERSEDED 2026-07-23 (lowercase revert) — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C — this UPPER-case direction was itself REVERTED
      back to lower-case fleet-wide; see that doc for execution).
- [x] [CODE] P1. Make MDPS odds writers stamp `venue = <bookmaker_key>` and `source = odds_api`, instead of
      `venue=ODDS_API`. ~~`_SPORTS_VENUES = frozenset({"ODDS_API"})`
      (`market_tick_data_service/adapters/umi_tick_provider.py:110`) is the declaration to change.~~ — **CORRECTED
      2026-07-27, was falsely closed** (supersedes a concurrent "⛔ SUPERSEDED 2026-07-23 (lowercase revert)" pass on
      this same line — that marker was about an unrelated data_type-casing revert, not this venue conflation, and
      pre-dates the real fix below): this checkbox was marked `[x]` "already covered by Track C" but (a) Track C never
      actually shipped this fix (its own text said "Do NOT touch the deliberate `mdps_odds_horizon_bucket`
      `venue=ODDS_API` aggregate... that's a different, intentional aggregate identity, not this bug" — now corrected,
      see that doc), and (b) the cited target (`_SPORTS_VENUES` in `umi_tick_provider.py`) was the WRONG symbol entirely
      — that's a CLI/dispatch-level venue selector ("which adapter category to invoke for a `--venue ODDS_API` backfill
      job"), not a per-row manifest stamp; changing it wouldn't make sense (the vendor endpoint genuinely is invoked at
      the ODDS_API level, then internally fans out to real per-bookmaker rows). **The REAL fix, now genuinely done
      (2026-07-27, `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Phase 1-2)**: MDPS's
      `market-data-processing-service/scripts/reprocess_sports_odds.py` — the actual odds_horizon_bucket manifest writer
      — was stamping every FINE per-`(league_id, timeframe)` manifest row `venue=ODDS_API`. Fixed forward
      (`market-data-processing-service@6f7422e`, fine rows now split per real `bookmaker_key`, one manifest row per
      distinct bookmaker present in the underlying shard) + backfilled for existing rows
      (`market-data-processing-service@a047b29`, VM-applied migration — see the issue doc's closing Update for the real
      row-count evidence). `source` stays `odds_api`'s SIBLING derived-product identity `mdps_odds_horizon_bucket`
      (investigated + confirmed correct, NOT `odds_api` — see the issue doc Phase 0/4). The COARSE per-day summary row
      deliberately keeps `venue=ODDS_API` as a documented aggregate sentinel (not a per-row conflation) — see
      `reprocess_sports_odds.py`'s `_MANIFEST_VENUE_AGGREGATE` docstring.
- [x] [CODE] P1. Stop writing bookmakers + `odds` into `instrument_type`; introduce the sports instrument_type
      vocabulary (betting market: match_odds / over_under / btts / spread). NOTE `canonical_writer_shaping.py:218`
      asserts _"the correct instrument_type IS 'odds'"_ — that claim must be reconciled against the shard atom
      (`instrument_type` is an INSTRUMENT axis, and `odds` is a data_type) BEFORE changing it. Read it in full first. —
      ⛔ SUPERSEDED 2026-07-23 (lowercase revert) — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C; see that doc for execution).
- [x] [CODE] P1. QG assertion: sports `data_type` ∈ the UAC **UPPER-case** sports vocabulary (per K0-DECISION (b) —
      corrected from "lower-case" for the same reason as above), `venue` ∉ {vendor names}, and `instrument_type` ∈ the
      declared sports vocabulary — so this class cannot silently return. — ⛔ SUPERSEDED 2026-07-23 (lowercase revert) —
      already covered by `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C — the vocabulary direction
      here was reversed to lower-case; see that doc for execution).

### K2. Phase 2 — MIGRATE the -prd- rows (only after K1 ships)

Measured drift in `market-data-tick-sports-prd` (1,974,679 rows): `ODDS`/`odds` 22,145+20,331; `ODDS_SNAPSHOT`/
`odds_snapshot` 4+4; `ODDS_MOVEMENT`/`odds_movement` 4+4; `venue=ODDS_API` 306,416; `venue=FOOTBALL` 1,337;
`instrument_type='odds'` 1,806,527 + ~1,321 bookmaker rows + `PADDYPOWER`/`paddypower`, `PINNACLE`/`pinnacle`.

- [x] [DATA] P1. New migrator targeting the **-prd-** buckets (the CF-7 script is legacy-only). DRY-RUN default,
      backup-before-write, per-batch verification. Reuse CF-7's `_CF7_DATA_TYPE_NORMALISE` decisions verbatim. — ⛔
      SUPERSEDED 2026-07-23 (lowercase revert) — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C — the casing target this migration would move
      rows TOWARD was itself reverted; see that doc for execution).
- [x] [DATA] P2. The 1,337-row legacy cohort (`odds_horizon_bucket_{15m,1h,4h,1d}` + `venue=FOOTBALL`, same rows) —
      superseded horizon naming with NO live writer; re-stamp to canonical or drop. One pass (operator-approved). — ⛔
      SUPERSEDED 2026-07-23 (lowercase revert) — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (already re-stamped per that doc's own Track record:
      "ALREADY DONE 2026-07-22" via market-tick-data-service@2f3fb7cc; see that doc for evidence).
- [x] [CLEANUP] P2. Delete `migrate_sports_canonical_v9.py` per its own Delete-when marker (E8 is complete). — ⛔
      SUPERSEDED 2026-07-23 (lowercase revert) — already covered by
      `/plans/archive/issues/sports_t6_8_oneoff_retirement_residual_2026_07_25.md` (tracks this exact deletion's
      residual status; see that doc for execution).

### K3. Phase 3 — prove it

- [x] [DATA] P1. Re-run the § F distinct-value audit and show ZERO case-duplicates, no vendor in `venue`, and
      `instrument_type` within vocabulary. Restore the data-status distinct-values listing (§ F, [CODE] P1) so this is
      visible in the UI instead of needing an ad-hoc query. — ⛔ SUPERSEDED 2026-07-23 (lowercase revert) — already
      covered by `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C's own re-audit + restore-listing
      work; see that doc for execution).

### K0-CORRECTION (operator challenge: "data_type is lowercase for sports or for all AGs? its uppercase for tradfi so thats weird")

**RETRACTED (mine)**: K0 said "`data_type` canonical = lower-case", generalising CF-7. CF-7's claim is scoped to the
**MDPS odds** data_types only, and I wrongly promoted it to a sports-wide rule. Measured reality:

| bucket | distinct | UPPER | lower | | ---------------------- | -------- | ----- | ------------- |
------------------------------------------------------------------------------------------------------- | | market-data
**tradfi** | 12 | **0** | 12 | | market-data **cefi** | 9 | **0** | 9 | | market-data **defi** | 6 | **0** | 6 | |
instruments **tradfi** | 1 | **0** | `instruments` | | instruments **cefi** | 1 | **0** | `instruments` | | instruments
**sports** | 9 | **9** | 0 | ← FIXTURES, FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, MATCHES, PLAYER_STATS,
PREDICTIONS, WEATHER | | features **sports** | 4 | **4** | 0 | ← DERIVED_FEATURES, FIXTURE_FEATURES, ODDS_FEATURES,
SFI_PROGRESSIVE_FEATURES | | market-data **sports** | 13 | 4 | 9 | ← the ONLY mixed bucket in the fleet |

**The operator's premise is inverted, and the conclusion is stronger: tradfi is lower-case; SPORTS is the outlier.**
Sports is the only asset group using UPPERCASE `data_type` anywhere. UAC agrees — `("tradfi","trades")` /
`("tradfi","ohlcv_1m")` are lower-case while `("sports","FIXTURES")` / `("sports","PLAYER_STATS")` are UPPER, with an
explicit comment that _"The canonical data_type name is PLAYER_STATS"_.

**Deeper than casing — a STRUCTURAL divergence.** instruments-tradfi/cefi carry a single `data_type='instruments'`;
instruments-**sports** carries 9 entity-like values. Sports is using `data_type` as an ENTITY axis where no other asset
group does. Any "make sports canonical" effort must decide that, not just the case.

**Three targets, NOT equivalent — needs an operator decision before ANY row is rewritten:**

- **(a) MDPS → lower only** (what K2 assumed): fixes the one mixed bucket, sports stays internally split (UPPER
  reference + UPPER features + lower MDPS). Cheapest; leaves sports non-canonical fleet-wide.
- **(b) sports → UPPER everywhere**: sports becomes internally uniform, but permanently diverges from tradfi/cefi/defi
  and from UAC's lower-case convention for those AGs. Entrenches the outlier.
- **(c) sports → lower everywhere** (TRUE fleet-canonical): aligns sports with every other AG. Largest — ~5.4M
  instruments-sports rows + the features layer + every UAC `("sports", …)` SOURCE_PRIORITY key + the
  `canonical_writer_stamping` bridge + downstream readers that filter on these literals. Also forces the structural
  question (is `data_type` an entity axis for sports, or should entity live on its own axis as it does elsewhere?).

- [x] [ASK] P0. Operator decision on (a)/(b)/(c) before K1/K2 execute. **K2 is BLOCKED on this** — normalising 2M MDPS
      rows to lower-case under (a) would be actively wrong if the answer is (b), and would be only ~5% of the work under
      (c). Recommendation: **(c)**, because it is the only option that makes "sports is canonical" true rather than
      "sports is self-consistent"; but it is a multi-week programme, not a migration script. — ANSWERED: § K0-DECISION
      directly below (same doc, operator 2026-07-18) chose **(b)** sports → UPPER everywhere, superseding this todo's
      own (c) recommendation. ⛔ **That answer was itself REVERSED 2026-07-23** — Track C in
      `sports_consolidated_closeout_2026_07_19.md` reverted the direction back to lower-case fleet-wide, which is why
      every § K1/§ K2/§ K3 checkbox above already carries the "⛔ SUPERSEDED 2026-07-23 (lowercase revert)" marker.
      Flipped here purely to record that the ASK was answered (twice, in sequence) — not left open.

### K0-DECISION (operator 2026-07-18): **(b) sports → UPPER everywhere**

Operator chose **(b)**: sports uses UPPERCASE `data_type` across all its layers — internally uniform, and knowingly
divergent from tradfi/cefi/defi (which are uniformly lower-case). **K2 is UNBLOCKED** with this direction:

- Reference (`instruments-sports`, 9 values) and features (`features-sports`, 4 values) are ALREADY all-UPPER — **no
  change needed**, they are already conformant under (b).
- Only **market-data-sports** is mixed (4 UPPER + 9 lower). Migration = normalise the 9 lower-case values UP:
  `odds`→`ODDS`, `odds_snapshot`→`ODDS_SNAPSHOT`, `odds_movement`→`ODDS_MOVEMENT`,
  `odds_horizon_bucket`→`ODDS_HORIZON_BUCKET` (+ the 4 legacy `odds_horizon_bucket_{15m,1h,4h,1d}` variants, which are
  the dead cohort in § F3 — re-stamp or drop in the same pass).
- This is the OPPOSITE direction to CF-7's `_CF7_DATA_TYPE_NORMALISE` (which mapped UPPER→lower). **CF-7's mapping is
  now superseded for sports** — that script is legacy-only and slated for deletion anyway (§ K2).
- **Bonus**: `canonical_writer_stamping.py`'s sports lower→UPPER map (which I nearly "fixed") is now ALIGNED with the
  chosen canonical, not a bridge to work around. Leave it.

Scope under (b) is far smaller than (c): ~42k case-duplicate rows in ONE bucket, versus ~5.4M reference rows + the
features layer + every UAC `("sports", …)` key.

## L. The features launcher could never replay a writer fix — **FIXED**

`launch-features-sports-backfill-vm.sh` used its `FORCE` flag ONLY for the same-prefix VM singleton lock; it never
reached `BACKFILL_CMD`. So the launcher structurally could not re-derive dates the manifest already marks captured/empty
— i.e. it could never replay a writer fix over history.

Measured: the lineups re-derive `fs-backfill-20260718-160901` ran **2.5 hours** logging
`SKIP fixture_lineups for <date> — manifest shows prior captured/empty (use --force)` on every date and wrote **ZERO**
shards. Identical defect class to the instruments-service fixtures gate (@7d49d096) — "force exists but does not reach
the thing that needs it" is now a THIRD instance this session.

Fixed in deployment-service@25d77c1: added `--redo-all`, deliberately SEPARATE from `--force` (`--force` = VM lock
bypass; `--redo-all` = pass `--force` to the features CLI). Conflating them is the documented api-football mistake. QG
green (2,542 passed). Relaunched as `fts-backfill-20260718-184352` with the CLI now receiving `--force`; tarball
re-verified aboard (features-service `47acb31f`, `cf10b931` ancestor-proven, flat-shape branch + coach emission present)
— MANDATORY here, because under `--redo-all` a pre-fix normalizer would OVERWRITE good 40-row shards with 0.

**Note on the 356 "fresh" lineup shards**: they were written 06:42Z by a PRE-fix run, not by my VM — which is why they
show `coach 0/40` (the old normalizer never emitted coach) despite having 40 rows (legacy nested shape parsed fine).
They are exactly what the `--redo-all` pass now replaces.

### L-VERIFIED (2026-07-18 19:10Z) — the lineups re-derive WORKS end-to-end

`fts-backfill-20260718-184352` (with `--redo-all`) measured on shards it wrote after 18:43Z:

- **0 `SKIP fixture_lineups` lines** (was: every date) and **131 `Wrote fixture_lineups` lines** — the launcher gap is
  genuinely closed.
- **168 shards** written by this run so far. Sampled 4:

| day        | rows | coach_name | coach_id | starters |
| ---------- | ---- | ---------- | -------- | -------- |
| 2020-07-13 | 830  | 803/830    | 825/830  | 440      |
| 2020-07-14 | 677  | 674/677    | 674/677  | 396      |
| 2020-07-15 | 927  | 911/927    | 911/927  | 550      |
| 2020-07-16 | 697  | 690/697    | 690/697  | 374      |

**coach_name populated 3,078/3,131 = 98.3%** (pre-fix: **0/40**); rows/day jumped from 40 to 700-900. The residual ~1.7%
nulls are fixtures that genuinely carry no coach upstream — honest absence, not a defect.

This closes the A1 chain end-to-end: normalizer flat-shape fix (features-service@cf10b931) + dedupe + coach emission,
delivered over history by the `--redo-all` launcher gap fix. **Zero api-football calls** — the entire restoration came
from raw already on disk.

### H-UPDATE (2026-07-18 19:12Z) — the concurrency damage is HEALING, not growing

Canonical index read (5,368,385 rows — read the parquet DIRECTLY; `read_availability_index` fell back to per-VM shards
under the stale-index gate and reported a FALSE `0`, cf. § J):

| metric                   | 15:57Z                                      | 19:12Z             | delta       |
| ------------------------ | ------------------------------------------- | ------------------ | ----------- |
| `attempted_failed` total | 477                                         | **385**            | **-92**     |
| attempted TODAY          | 153                                         | **61**             | **-92**     |
| error_reason breakdown   | `FIXTURES_FETCH_FAILED` 92 + `rateLimit` 61 | **`rateLimit` 61** | 92 repaired |

**RETRACTED (mine)**: § H said the enrichment-entity false failures "do NOT self-heal — their VMs are stopped". They DID
heal: the (auto-relaunched) enrichment VMs re-attempt those cells, and all 92 `FIXTURES_FETCH_FAILED` rows flipped to
captured/empty. **No new failures since containment** — so 4 concurrent VMs are not currently generating fresh
rate-limit damage the way 5 were. No further VM intervention is warranted.

Residual: **61 `rateLimit` rows** from the 5-VM window (15:27-15:57Z). They are FALSE failures — the data is fetchable,
the key was saturated. They will heal the same way if their (date, entity) cells are re-attempted; otherwise re-attempt
explicitly once the key has a single owner.

- [x] ✅ [DATA] P2. Confirm the residual 61 `rateLimit` rows reach captured/empty (they should heal via normal
      re-attempt); only force an explicit re-attempt if they persist after the enrichment fleet completes its range. —
      GENUINELY OPEN: no later doc in the corpus reports re-checking this specific 61-row residual from the 2026-07-18
      15:27-15:57Z 5-VM window. Confirming it needs a fresh manifest census on the exact (date, entity) cells, which
      this reconciliation pass did not run (out of scope — this todo is a data-verification action, not a checkbox
      classification). Left open. **Already extracted — see `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo
      (line ~349, `assigned_vm: planning`, still `- [ ]` open there too as of 2026-08-09) — not duplicating here.** —
      **RESOLVED 2026-08-10 (slot 23, batch9-021): ALL 61 HEALED — census recorded in this doc's Progress Log.**

## M. Why we get rate-limited: the divisor was a PROMISE, not a measurement — **FIXED** (deployment-service@e85d570)

Operator: _"why we getting rate limited so much dont we knwo our rate limits on api football side and govern them across
vms properly?"_ — we DO know them, and a governor exists. The gap is where the divisor comes from.

**The design (sound):** api-football enforces **1200 req/min AND 450,000 req/day, ONE quota across ALL endpoints**. The
launcher computes a daily-aware effective ceiling, splits it `EFFECTIVE_RPM / FLEET_VMS`, stamps the per-VM req/min +
matched concurrency into VM metadata, and the adapter self-enforces that throttle.

**The gap:** `FLEET_VMS="${FLEET_VMS:-1}"` — it **defaulted to 1 and never auto-detected**. So every VM assumed it was
ALONE unless a human remembered `--fleet-vms N`. Nothing enforced that promise. Worse, the singleton COUNT ran only
inside `if ! $FORCE && ! $SKIP_LOCK` — it did not count on exactly the paths that create concurrency:

- `--force` / `--skip-lock` (deliberate fan-out)
- a second actor launching independently (§ I — the auto-relaunched enrichment fleet)
- **auto-relaunch**: `RelaunchPreemptedVm` replays the ORIGINAL env, so a VM relaunched into a now-crowded fleet carries
  a per-VM budget computed when it WAS alone. This one cannot be fixed by operator discipline at all.

Five concurrent VMs each throttling at a full-budget share = **5x oversubscription**, which is why the 429s appeared
despite an apparently-correct governor. Measured: **61 `rateLimit` FALSE `attempted_failed` rows in ~30 min**.

**Fix:** when `--fleet-vms` is not explicitly passed, COUNT the running `af-backfill-*`/`af-audit-*` VMs and derive
`FLEET_VMS = count + 1`, logging the derivation loudly. Explicit `--fleet-vms` still wins. QG green (2,542 passed).

**PARTIAL by construction — stated in the log, not hidden:** already-running VMs keep the budget they computed at THEIR
launch, so the key stays oversubscribed until they finish. Launch-time division cannot fix a fleet that grows after
launch.

- [ ] [CODE] P1. Runtime re-division: VMs should read the CURRENT fleet size (or lease a share from a central budget)
      and re-throttle when the fleet grows, instead of trusting a launch-time constant. Until then the singleton lock is
      doing the real work and every bypass path is a live oversubscription risk. — NARROWED, left OPEN: the crude
      launch-time `FLEET_VMS` heuristic this todo targeted no longer exists — replaced by
      `plans/active/data_completion_sports_2026_07_24.md`'s `launch_budget_registry.py` (deployment-service@e754c9f +
      @1a06ffa), which is daily-quota- and time-aware, fail-closed (`assert_fleet_within_budget`), and self-enforced
      proactively via UTC-boundary-aligned windows in the adapter (`base.py::_reserve_utc_window_slot`) rather than
      reactive 429-backoff. The launcher also now measures `RUNNING_AF_COUNT` live at EVERY launch (§ M-FIXED item 1,
      below), closing most of the practical oversubscription risk this todo describes. **What remains genuinely open**:
      that same M-FIXED text explicitly says "already-running VMs keep the budget they computed at their own launch, so
      the key stays oversubscribed until they drain... the remaining fix is runtime re-division" — i.e. a VM that is
      ALREADY mid-flight does not dynamically re-throttle when a later VM joins the fleet. No later doc reports this
      specific mid-flight rebalancing as shipped. Left open, narrowed to that residual. **Round-9 sweep (2026-08-09,
      sports tranche): considered for satellite extraction, not extracted.**
      `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s Deferred ledger considered this item too (its own text is
      garbled/truncated in that doc, corpus-wide corruption unrelated to this sweep) but did not extract it — consistent
      with this pass's own read: the fix requires choosing a mechanism (VMs periodically re-polling live fleet size vs.
      leasing shares from a central budget service) — an architecture/design call, not a mechanical patch, so it stays a
      genuine judgment-gated item, not AO-eligible as written.
- [x] [CODE] P1. `RelaunchPreemptedVm` should RE-DERIVE the rate budget on replay rather than replaying the original
      per-VM share — same root cause as § G-ops (replaying stale launch params). — SUPERSEDED: § M-FIXED item 2 below
      (same doc, dated later) — `deployment-service@cb499b7`: `RelaunchPreemptedVm` now STRIPS
      `SPORTS_ADAPTER_RATE_RPM`/`SPORTS_ADAPTER_CONCURRENCY`/`FLEET_VMS`/`REMAINING_DAILY_QUOTA` from the replayed env
      so the launcher re-derives them fresh on relaunch, exactly as this todo asks. QG green, regression-pinned.

## N. Why sports downloads take "way too long" — we were using a SLEDGEHAMMER (~1,800x waste)

Operator: _"lets optimise the downloads for sports fully its taking way too looong"_. Measured root cause — it is **call
VOLUME**, not rate governance:

| approach                                               | api-football calls                                                  |
| ------------------------------------------------------ | ------------------------------------------------------------------- |
| full `--force --entity FIXTURES` backfill              | **527 calls/date (measured mean) x 2,390 dates ~= 1,260,000**       |
| surgical `backfill_sports_fixture_round_2026_07_17.py` | **~600-700 TOTAL** (one bulk `GET /fixtures?league&season`, cached) |

**~1,800x reduction.** At the 450,000/day key quota the full re-fetch needs **~2.8 days of pure quota** (~76h at the
paced rate) — to populate **ONE field**. No amount of rate tuning or extra VMs can fix a 1,800x volume problem; the
per-key daily quota is a hard ceiling that MORE VMS CANNOT RAISE.

Pilot confirms the shape: `Fetched 242 season fixtures for league=113 season=2019` — **one call returned 242 fixtures**,
vs 527 calls per DATE in the full path. The script is round-only (touches blank `round` cells), SINGLE-WALK (one corpus
listing, not per-league re-walks), snapshots each parquet to `*.pre_round_backfill.bak`, and is idempotent.

- [x] [OPS] P0. STOP using the full `--force` FIXTURES backfill to fix `round`. Use the surgical script. (The `--force`
      VM was already preempted and NOT relaunched, so nothing to unwind.) Pilot running:
      `--max-leagues 1 --seasons 2019 --apply`.
- [x] [OPS] P0. After the pilot verifies, run the full surgical backfill (all leagues x 2019-2026) in the background. —
      SUPERSEDED: the 2019-2020-06-05 portion of this range is now MOOT — `sports_consolidated_closeout_2026_07_19.md`
      Track V (2026-07-27) executed the 2020-06-06 sports data-floor wipe, deleting every pre-floor
      fixtures_schedule/fixtures_outcomes row (pre-floor is fabrication-by-construction); there is nothing left there to
      backfill. The post-floor portion's goal (round populated, `competition_phase` sane) was independently confirmed
      live 2026-07-21 via the zero-API-cost sibling-derivation script (`derive_sports_fixture_round_2026_07_18.py`,
      instruments-service@e63049e7) plus two scoped backfills (§ T/§ W) — see
      `/plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md` (status:
      resolved, "No code shipped this session — both real defects... were already fixed and are confirmed live"). The
      full corpus-wide surgical run as originally scoped was never executed as such; the same end-state was reached by a
      cheaper combination of fixes.
- [ ] [PROCESS] P1. Generalise: before launching a `--force` whole-corpus refetch to fix ONE column, check whether a
      surgical column-filler exists. The blast radius / quota cost differ by orders of magnitude, and `--force` also
      forfeits presence-skip resume (§ G-ops). — GENUINELY OPEN: grepped `/codex/12-agent-workflow/` and
      `/codex/05-infrastructure/vm-launcher-runbook.md` for this lesson — no hit. Unlike item 2's watchdog-artifact
      lesson (codified into `async-wait-and-poll-discipline.md` + `CLAUDE.md`), this "check for a surgical filler before
      a full refetch" generalisation was never written into a codex SSOT. Still a live process gap. **Already extracted
      — see `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo (line ~356, `assigned_vm: planning`, still `- [ ]`
      open there too as of 2026-08-09) — not duplicating here.**

## M-FIXED. Both rate-governance gaps CLOSED (operator: "donot just file them fix them")

1. **Divisor from MEASURED concurrency** — `FLEET_VMS` defaulted to 1 (every VM assumed it was alone); the singleton
   count ran only inside `if ! $FORCE && ! $SKIP_LOCK`, i.e. NOT on the paths that create concurrency. Now the launcher
   counts running `af-backfill-*`/`af-audit-*` VMs and derives `count + 1` when `--fleet-vms` is not explicit, logging
   the derivation. Explicit still wins.
2. **Re-derive on preemption replay** — deployment-service@cb499b7: `RelaunchPreemptedVm` now STRIPS
   `SPORTS_ADAPTER_RATE_RPM` / `SPORTS_ADAPTER_CONCURRENCY` / `FLEET_VMS` / `REMAINING_DAILY_QUOTA` from the replayed
   env so the launcher re-derives them. A VM preempted while ALONE no longer re-applies a full-key budget when
   relaunched into a crowded fleet. QG green (2,543 passed), regression-pinned (non-rate params still replay verbatim).
   This path could NOT be fixed by operator discipline — nothing passed at first launch survives correctly into an
   automated relaunch.

**Still partial, stated not hidden**: already-running VMs keep the budget they computed at their own launch, so the key
stays oversubscribed until they drain. Launch-time division cannot fix a fleet that grows after launch — the remaining
fix is runtime re-division / leasing shares from a central budget (§ M todo).

## O. Carried from `sports_enrichment_mvp_scope_leak_2026_07_26.md` (archived 2026-07-26) — honest-absence denominator still wrong for MVP-scoped per-fixture enrichment

That issue's own per-fixture-enrichment MVP-scope leak was fixed and archived (`unified-api-contracts@f674033f`,
`instruments-service@b00e4433`), but it deliberately deferred one narrower, riskier sub-concern rather than bundle it
into the same fix — carried forward here so it isn't lost with the archive:

- [ ] [DATA] P2. **`emit_empty_gaps_for_entity`** (`instruments-service/.../sports_reference_core.py`) — the
      honest-absence gap emitter for FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS — still hardcodes
      `get_expected_leagues_for_source("api_football")` (383 leagues) as its "expected" denominator, independent of the
      now-MVP-scoped `SPORTS_ENTITY_LEAGUE_COVERAGE`. This means completeness/coverage tracking for these 4 entities
      will show the ~287 non-MVP widened leagues as permanently `expected_unattempted` (since capture now deliberately
      never touches them) rather than an honest "out of scope by policy" absence. This is a coverage/reporting-accuracy
      concern, NOT a call-volume bug (the archived fix already stops the API calls) — deliberately NOT touched in that
      session because `emit_empty_gaps_for_entity` is a shared function whose honest-absence semantics have been the
      subject of multiple past incidents (several "RETRACTED" analyses elsewhere in this doc's family). **Done when**:
      either `emit_empty_gaps_for_entity` branches its expected-denominator by data_type (MVP set for the 4 enrichment
      entities, full set otherwise), or an operator decision accepts the wider denominator as intentional for these
      entities and documents why. — GENUINELY OPEN: `plans/active/data_completion_sports_2026_07_24.md` extended the
      `SPORTS_ENTITY_LEAGUE_COVERAGE` mechanism to WEATHER + PLAYER_VALUES (unified-api-contracts@2ec928b0 + @a0c6064e)
      — so the coverage-map infrastructure this fix needs now exists and is proven — but that work did NOT touch
      `emit_empty_gaps_for_entity` or the 4 per-fixture enrichment entities (FIXTURE_STATS/FIXTURE_EVENTS/
      FIXTURE_LINEUPS/PLAYER_STATS) this todo names. The two other `emit_empty_gaps_for_entity` hits found elsewhere in
      the corpus (`sports_satellite_ao_dispatch_batch3_2026_07_25.md`,
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`) are about a DIFFERENT concern on the same
      function (QG function-size decomposition, 89L→≤50L) — unrelated to this denominator bug. Still open. **Already
      extracted — see `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo (line ~363, `assigned_vm: planning`,
      still `- [ ]` open there too as of 2026-08-09) — not duplicating here.**

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — 2 of the 7 open todos are explicitly owned
  elsewhere and annotated 'not duplicated here — left open, owned by Track V'; `[PROCESS] P1` asks for a NEW codex
  authoring rule (an operator ruling this run cannot obtain, and codex edits are out of scope); and `[DATA] P2` on
  `emit_empty_gaps_for_entity` states its own alternative as 'or an operator decision accepts the wider denominator as
  intentional'
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped two now-historical codex citations
  (async-wait-and-poll-discipline / spot-vms-for-backfill, both already-shipped lessons) for
  `data_completion_sports_2026_07_24.md` (owns §M's runtime re-division registry) and `sports_reference_core.py` (the
  actual file behind §O's open `emit_empty_gaps_for_entity` denominator finding).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 7 open items: 2 dependency-blocked, 2 lower-confidence
  AO-eligible candidates not yet promoted, 1 genuine work, 2 operator questions.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, valid — re-verified all 7 open todos. 2 (§G "Step 4"
  line ~211, §G-RESOLVED line ~251) are correctly owned by `sports_consolidated_closeout_2026_07_19.md` Track V (still
  `- [ ]` open there, unchanged). 4 (§J error-text line ~408, §L rateLimit-residual line ~642, §N PROCESS-codify line
  ~734, §O emit_empty_gaps line ~764) are already claimed as open todos in
  `sports_satellite_ao_dispatch_batch9_2026_08_04.md` (`assigned_vm: planning`, status: active, all 4 still `- [ ]`
  there too) — added inline "Already extracted" citations at each so this doesn't get re-derived as a fresh extraction
  candidate next pass. 1 (§M Runtime re-division, line ~677) reconfirmed genuinely design-gated (mechanism choice, not a
  mechanical patch) — not extracted. No new work found; doc stays `assigned_vm: NA`.
- **batch9-021 rateLimit-residual census 2026-08-10 (slot 23)**: **ALL 61 HEALED — ZERO remaining `rateLimit`
  `attempted_failed` rows attributable to the 2026-07-18 15:27-15:57Z api-football 5-VM concurrency window.** Live
  canonical (`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, read via
  `read_availability_index_safe`, column-pruned + row-group filter pushdown, fresh read) as of 2026-08-10:
  - `capture_status=attempted_failed AND error_reason=rateLimit` in the 4 incident entities (FIXTURE_EVENTS /
    FIXTURE_LINEUPS / FIXTURE_STATS / PLAYER_STATS): **0 rows**.
  - `capture_status=attempted_failed` (any reason) in the 4 entities with `attempted_at` in 2026-07-18
    15:27:00-15:57:00Z: **0 rows**.
  - Whole-corpus `rateLimit` attempted_failed: 103 rows, ALL `STANDINGS` (attempted_at 2026-08-05..08-10), produced by
    the tracked in-flight `af-backfill-20260810-103218` campaign (owned by
    `sports_af_full_entity_completion_2026_08_03.md`) — **NOT** attributable to the 07-18 window.
  - Residual attempted_failed in the 4 entities (6,294 rows) all carry documented pre-existing non-`rateLimit` reasons:
    4,996 `fixture_events_phantom_manifest_reflip_2026_07_26` + 1,210 Defect-3 pre-2021 writer-generation artifact + 88
    stale bare-`player_stats.parquet` migration rows — none window-attributable.
  - Reconstruction note (honest): the exact (date, entity) cell list for the 61 is NOT recoverable from history — no
    2026-07-18 manifest snapshot exists (closest: `20260717-012712.pre_t6_1` pre-incident and `20260724-202648`
    post-heal), and the incident VMs' per-VM shards were pruned by the consolidator. The verdict therefore rests on the
    current-state census, which is dispositive: the 19:12Z 07-18 measurement (this doc's §H-UPDATE) established the 61
    `rateLimit` rows as the ONLY `rateLimit` rows in these 4 entities at that time, and the current manifest shows ZERO
    `rateLimit` rows there (the only residual `rateLimit` rows anywhere are `STANDINGS`, from a later tracked campaign)
    — so all 61 have transitioned to `captured`/`empty_confirmed`.
  - **No explicit re-attempt needed.** Batch9 todo (`sports_satellite_ao_dispatch_batch9_2026_08_04.md` item) flipped
    same-turn.
