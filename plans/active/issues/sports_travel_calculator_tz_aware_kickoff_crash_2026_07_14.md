---
doc_type: issue
title:
  features-service sports travel_calculator silently NaN'd travel/cumulative-travel columns for every tz-aware
  kickoff_utc fixture — fixed, backfill re-run of affected dates still owed
summary: >
  While re-verifying sports_p2_features_history_to_ml_ready-002 (Todo 3, still structurally BLOCKED-PREREQ on Todo 1's
  in-progress 2015→present compute), found `travel_calculator.compute_travel_batch` (features-service) raising
  `ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter` on
  `pd.Timestamp(fixture["kickoff_utc"], tz="UTC")` whenever `kickoff_utc` arrives already tz-aware. The per-fixture
  shard-level try/except (by design, for genuine failure isolation) caught it and silently defaulted
  `away_cumulative_travel_30d` / `home_cumulative_travel_30d` / `*_travel_per_game_30d` / `travel_fatigue_ratio` to NaN
  — 8,648 occurrences on ONE of the 3 currently-running gap-fill VMs (`features-sports-sports-20260714-085703`) within
  ~3h of live backfill traffic. This is a code-defect NaN, not an honest-absence NaN (the data existed and was
  computable) — it just wasn't typed/counted as a failure anywhere. Fixed in features-service@d878f11a (switched to
  `pd.to_datetime(..., utc=True, errors="coerce")`, matching the tz-naive/tz-aware normalization already used for
  `fixtures_history` two lines above). The 3 VMs currently running the P2c 2015→present backfill are on a pre-fix
  tarball snapshot and will keep producing these silent NaNs on every tz-aware-kickoff fixture until relaunched or until
  a targeted gap-fill re-run picks up the fix.
status: resolved
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, travel-calculator, honest-absence, timezone, silent-failure]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-14
parent_epic: sports_master
priority: P2
source: sports_p2_features_history_to_ml_ready-002 dispatch, slot 12, 2026-07-14 (Todo 3 re-verify, log-tail dive)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
  - sports_p2_features_history_to_ml_ready_2026_06_27.md
gate_on_depends: true
last_updated: 2026-07-20
locked_by:
resolved_by: features-service@d878f11a
---

# features-service sports travel_calculator silent NaN on tz-aware kickoff_utc

## What I found

`features_service/sports/calculators/travel_calculator.py:258` (pre-fix):

```python
match_date = pd.Timestamp(cast(object, fixture["kickoff_utc"]), tz="UTC")
```

`pd.Timestamp(value, tz="UTC")` raises
`ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter. Use tz_convert instead.` whenever
`value` already carries tzinfo. `compute_travel_batch`'s per-fixture loop wraps the whole body in
`except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, ArithmeticError, OSError):` (correct
shard-level-isolation design — no `raise` inside a per-fixture loop), which caught this and logged
`"Travel calc failed for fixture %s, defaulting to NaN"` before defaulting the whole row's `TRAVEL_COLUMNS` to NaN.

Confirmed live-scale via the run.log of one of the 3 currently-running P2c backfill VMs
(`features-sports-sports-20260714-085703`, `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`):
**8,648** "Travel calc failed" warnings between 09:11:47Z and 11:52:57Z (~2h41m) — every one the identical `ValueError`
traceback, i.e. every fixture whose `kickoff_utc` happened to already be tz-aware on read. The other 2 VMs (`-085642`,
`-085726`) were mid different date ranges at inspection time and not directly sampled for this specific warning, but run
the identical code path.

Two of `TRAVEL_COLUMNS`' six fields are gated behind this one `pd.Timestamp` call
(`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`away_travel_per_game_30d`/`home_travel_per_game_30d`/
`travel_fatigue_ratio` — everything past the point-to-point `*_travel_distance_km`/`*_is_long_travel`/
`travel_distance_diff` fields, which compute fine before this line). So this is a partial-row degradation, not a
whole-row blank — but for every affected fixture the 5 cumulative-travel columns are code-defect NaN, not honest
upstream absence, and nothing distinguishes the two in the written parquet (both are just NaN).

## Why it matters

- Violates the data_engineering craft's north-star #1 (no silent placeholders — a computable value silently degraded to
  NaN by a code bug must not be indistinguishable from a genuine honest-absence NaN).
- At 8,648 occurrences on one VM in <3h, this affected a large fraction of the 2015→present sports backfill
  `sports_p2_features_history_to_ml_ready-002` (Todo 1) is currently running — likely tens of thousands of fixtures
  fleet-wide by the time that backfill completes, unless re-run with the fix.
- Directly relevant to this plan's Todo 2 gate ("every NaN traces to a typed upstream honest-absence") — these NaNs do
  NOT trace to honest absence, they trace to a code defect. Todo 2 already found the Todo-2 gate failing for other
  reasons (compute not yet complete) and is slated for re-run once Todo 1 finishes; that re-run should also sample
  cumulative-travel columns specifically, now that the code-side cause is fixed.

## Recommended decision

Fix now (small, clear, root-caused) — **done**, shipped features-service@d878f11a. Remaining question is operational,
not a design decision: the 3 already-running P2c backfill VMs are on a pre-fix snapshot and won't pick up the fix
without a relaunch or a targeted gap-fill re-run. Given the backfill is >55% through history and healthy (per this
plan's extensive Progress Log), killing and relaunching the live VMs now to force-adopt the fix is a bigger, riskier
action than this finding warrants on its own — recommend letting the current pass finish, then gap-filling the affected
date-ranges (identifiable via `--force` re-run scoped to dates whose parquet cumulative-travel columns are all-NaN, once
the fix is in the deployed tarball) as a normal follow-up backfill pass.

## Todos

- [x] [DATA] P1. **Fix the tz-handling bug** in `travel_calculator.compute_travel_batch` — replace
      `pd.Timestamp(fixture["kickoff_utc"], tz="UTC")` with
      `pd.to_datetime(fixture["kickoff_utc"], utc=True,     errors="coerce")` (matches the fixtures_history
      normalization 2 lines above). (repo: features-service) — features-service@d878f11a, QG green, shipped via
      quickmerge --agent 2026-07-14.
- [x] ✅ [DATA] P2. **After `sports_p2_features_history_to_ml_ready-002` Todo 1 (2015→present compute) reaches
      completion**, identify date-ranges computed BEFORE features-service@d878f11a landed (2026-07-14) whose
      `sports_features/by_date/day=*/feature_group=*` cumulative-travel columns
      (`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`*_travel_per_game_30d`/`travel_fatigue_ratio`) are
      suspiciously all-NaN for dates with tz-aware `kickoff_utc` fixtures, and gap-fill re-run those with `--force` on
      the fixed code. (repo: features-service) — **Verified NO gap-fill needed**: content-sampled 7,641 real rows across
      3 independent samples (46 dates spread 2017-2026; the exact 111-date/1,558-shard window matching the documented
      08:56-12:20:33Z 2026-07-14 crash window; the freshest live day 2026-07-16) — the tz-crash's specific "all 5 travel
      columns NaN" pattern occurs in **zero** rows. Found a different, bigger, still-open defect instead (home-side
      venue-coordinate lookup failing near-universally, cumulative-travel hardcoded to 0.0 corpus-wide, including in
      current-live data) — filed as its own issue doc:
      `plans/active/issues/sports_travel_calculator_home_venue_coords_never_resolved_2026_07_17.md` (P1, 3 todos). See
      that doc for full evidence; not absorbing into this issue doc's scope since it's unrelated to the tz-crash this
      doc tracks. slot-4, 2026-07-17.
- [x] ✅ [DATA] P3. **Audit whether other sports calculators share the same
      `pd.Timestamp(value, tz="UTC")`-on-possibly-aware-value pattern** — grepped
      `features_service/sports/calculators/*.py` for `tz="UTC"`/`tz=UTC`, found 7 call sites, checked each: -
      **`european_fatigue_calculator.py:207`** — IDENTICAL bug (`match_date = pd.Timestamp(raw_date, tz="UTC")` on the
      same `kickoff_utc` column), and WORSE than travel_calculator's: `match_date` gates the ENTIRE row (all
      `EUROPEAN_FATIGUE_COLUMNS`), not just a subset. Confirmed live-scale on the 3 running P2c backfill VMs: **33,348**
      occurrences on `-085703`, **261** on `-085642`, 0 on `-085726` (mid a different date range). Fixed —
      features-service@81036512 (same `pd.to_datetime(utc=True, errors="coerce")` swap). - `manager_calculator.py:522`,
      `season_context.py:319` — `tz="UTC"` only reached via the `pd.Timestamp.now(tz="UTC")` fallback branch (always a
      fresh timestamp, never re-parses a possibly-aware value) — NOT vulnerable. - `h2h_calculator.py:283` —
      `pd.Timestamp.now(tz="UTC")`, same as above — NOT vulnerable. - `european_fatigue_calculator.py:157` — string
      literal `f"{season_year}-07-01"`, always naive — NOT vulnerable. - `transfer_window_calculator.py:378` —
      `match_date.isoformat()` where `match_date: date` (not `datetime`) per the function signature, so `.isoformat()`
      is always a bare `YYYY-MM-DD` with no tzinfo — NOT vulnerable. **Gate met**: audited all 7 sites; found + fixed 1
      additional real instance (the other 6 are safe by construction). No further sports-calculator instances of this
      exact pattern remain.

## Progress Log

### 2026-07-14T12:5x UTC — data_engineering slot-6 (Todo 2 dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 (identify + gap-fill pre-fix all-NaN cumulative-travel date-ranges) — still BLOCKED-PREREQ.** This todo's own
text is explicit: "After `sports_p2_features_history_to_ml_ready-002` Todo 1 (2015→present compute) reaches completion".
Checked `sports_p2_features_history_to_ml_ready_2026_06_27.md`'s own Progress Log (dozens of prior `Todo 1`/`Todo 3`
re-dispatch entries, most recent at 12:33 UTC) — Todo 1 is still `[ ]`, genuinely in-progress multi-day compute.
Independently re-verified via non-snap `gcloud`/`gsutil` (`/home/ubuntu/google-cloud-sdk/bin/`): same 3 VMs
(`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same creation timestamps; features bucket
unique-date count **2,519** (up from 2,502 at the 12:33Z parent-plan check ~20 min earlier) — steady forward progress
(~59.8% of ~4,210-day history), no stall, no crash. Identifying pre-fix all-NaN date-ranges before Todo 1 finishes would
be premature (the affected-range boundary isn't stable until the full-history compute completes). Declining — no action
taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T13:0x UTC — data_engineering slot-3 (Todo 2 re-dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Same structural gate as slot-6's check above. The parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` was independently touched 3 minutes before this dispatch by two
sibling slots (15 @ 12:48 UTC, 16 @ 12:33/12:50 UTC): Todo 1 confirmed still `[ ]` at ~59.8% coverage (2,519/4,210
unique dates), Todo 3 still BLOCKED-PREREQ. Re-confirmed independently via non-snap `gcloud compute instances list`: all
3 backfill VMs (`features-sports-sports-20260714-085642/-085703/-085726`) still `RUNNING`, same creation timestamps as
every prior check — no stall, no crash, steady progress. Given the prereq state was verified fleet-wide 3 minutes ago by
two other slots, skipping the redundant full GCS-walk this dispatch (single-walk discipline — no value in a 4th
identical corpus scan in under 20 minutes). Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-14T12:55 UTC — data_engineering slot-15 (Todo 2 re-dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 (identify + gap-fill pre-fix all-NaN cumulative-travel date-ranges) — still BLOCKED-PREREQ, unchanged.** This
todo's own text is explicit: "After `sports_p2_features_history_to_ml_ready-002` Todo 1 (2015→present compute) reaches
completion". Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 confirmed still `[ ]` — this same
slot's own entries there ~5-8 min earlier (12:47/12:50 UTC) already found the fleet healthy at 2,519/4,210 (~59.8%).
Cheap independent re-check this dispatch (non-snap `gcloud`/`gsutil`, `central-element-323112`): same 3 VMs
(`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same creation timestamps; features bucket
unique-date count **2,525** (up from 2,519 ~8 min earlier, +6) — steady forward progress, no stall, no crash. The
affected-range boundary for this todo's gap-fill isn't stable until Todo 1's full-history compute completes, so starting
the identify/gap-fill work now would be premature. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-14T13:09 UTC — data_engineering slot-16 (Todo 2 re-dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Same structural gate as the three prior re-checks above. Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 confirmed still `[ ]` (this same slot's own 12:28 UTC
entry there already found the fleet healthy at 2,502/4,210). Cheap re-check this dispatch (non-snap `gcloud`/`gsutil`,
`central-element-323112`): same 3 VMs (`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same
creation timestamps; features bucket unique-date count **2,538** (up from 2,525 ~14 min earlier per slot-15's check,
+13) — steady forward progress, ~60.3% of ~4,210-day history, no stall, no crash. The affected-range boundary for this
todo's gap-fill still isn't stable until Todo 1's full-history compute completes. Declining — no action taken, no code
touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T13:12 UTC — data_engineering slot-9 (Todo 2 re-dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Same structural gate as every prior re-check above, this one only 3
minutes after slot-16's. Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 confirmed still `[ ]`
(grepped the plan directly). Cheap non-GCS-walk re-check (`gcloud compute instances list`, `central-element-323112`):
same 3 VMs (`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same creation timestamps — no
crash, no stall. Skipping a redundant full-corpus GCS date-count walk given slot-16 ran one 3 minutes ago (single-walk
discipline — no value in a 5th identical scan within 20 minutes). The affected-range boundary for this todo's gap-fill
still isn't stable until Todo 1's full-history compute completes. Declining — no action taken, no code touched, checkbox
NOT flipped. `/skip-current-task`.

### 2026-07-14T13:2x UTC — data_engineering slot-13 (Todo 2 re-dispatch — still BLOCKED-PREREQ, cheap re-check only)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Same structural gate as every prior re-check above (this is the 7th
consecutive dispatch of this exact todo). Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` (grepped the plan's checkbox list directly). Cheap non-GCS-walk
re-check (`gcloud compute instances list`, `central-element-323112`, non-snap binary): same 3 VMs
(`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same creation timestamps as every prior check
— no crash, no stall. Skipped a redundant full-corpus GCS date-count walk (single-walk discipline — slot-9 ran one ~10
min earlier; no value in an 8th identical scan). The affected-range boundary for this todo's gap-fill still isn't stable
until Todo 1's full-history compute completes. Note for main/operator: this backlog task has now round-tripped through 7
slots without a structural prereq gate (its dependency on Todo 1 is prose-only, inside its own todo text, not a
`prereqs.completed_tasks` binding) — consider parking it (RULES.md § "Park a task") against Todo 1's completion to stop
the redispatch churn. Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T14:0x UTC — data_engineering slot-14 (Todo 2 re-dispatch — still BLOCKED-PREREQ, 8th consecutive check; filed parking escalation)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Same structural gate as all 7 prior re-checks. Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
(grepped the plan's checkbox list directly). Cheap non-GCS-walk re-check (`gcloud compute instances list`,
`central-element-323112`, non-snap binary): same 3 VMs (`features-sports-sports-20260714-085642/-085703/-085726`) all
`RUNNING`, no crash. Skipped the redundant full-corpus GCS date-count walk (single-walk discipline — 8 identical scans
in under 2h has no marginal value). **This is now the 8th slot burned on the same structural gap** — rather than add a
9th "consider parking it" note, I located the concrete blocker: the live orchestrator's `data/config/backlog.yaml` that
`park a task` (RULES.md §4) needs to edit lives in the **root PM/agent-orchestrator clone**
(`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/config/backlog.yaml`), which is READ-ONLY for a
worker slot per RULES.md's root-clone hard rule — I cannot make this edit myself from `.tabs/14`. Filed `/blocked`
(`BLK-` — see slot heartbeat) asking main/operator to apply the exact recipe: set `priority: 999` +
`priority_override: true` + `prereqs.prerequisites: [sports-p2-todo1-2015-present-complete]` (condition created `false`
via `POST /api/prerequisites/...`, flipped `true` once Todo 1's checkbox lands) on this task's entry, then
`POST /api/backlog/reload`. Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T14:2x UTC — data_engineering slot-15 (Todo 2 re-dispatch — 9th consecutive check; found the parking recipe was only HALF-applied)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep. Cheap non-GCS-walk re-check
(`gcloud compute instances list`, `central-element-323112`, non-snap binary): same 3 VMs
(`features-sports-sports-20260714-085642/-085703/-085726`) all `RUNNING`, same creation timestamps — no crash, no stall.
Skipped a 9th redundant full-corpus GCS date-count walk (single-walk discipline).

**New finding**: queried the live backlog via `curl $SERVER_URL/api/backlog` — this task's entry now shows
`"priority": 999` (main/operator DID act on slot-14's `/blocked` — the priority half of the recipe landed) but there is
NO `prereqs.prerequisites` field on the entry, and `target_slot`/`affinity` are still `none`/default. So the structural
condition gate (`sports-p2-todo1-2015-present-complete`) from slot-14's recipe was never created/attached — that's WHY
this keeps getting redispatched: `priority: 999` only deprioritizes, it doesn't structurally block, so whenever no other
task is eligible the dispatcher still calls this "highest-rank queued task with prereqs met" (confirmed: that's the
literal `dispatch_reason` on my own `/boot` this dispatch). Verified the live file lives at
`agent-orchestrator/data/config/backlog.yaml` in the **root** clone (confirmed via `ps aux` — the running uvicorn
server's cwd is the root `agent-orchestrator` clone, not any `.tabs/<N>` slot), so this is genuinely outside a worker's
write scope, not a availability gap I'm missing.

Not re-filing a duplicate `/blocked` (slot-14's is presumably still open/unanswered — no message received on this boot).
Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T23:3x UTC — data_engineering slot-8 (Todo 2 re-dispatch — 10th consecutive check; parking recipe confirmed reverted, not just half-applied)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep after fresh-pull to LDR HEAD (`06476f2dc`).
Coverage check (bounded day-prefix listing, `gsutil ls -d .../by_date/day=*/ | wc -l` — NOT a whole-corpus walk):
**2,888/4,210** unique dates (~68.6%), up from slot-15's 2,538 at 13:09 UTC — real forward progress over the last ~10h,
but genuinely incomplete.

**New finding — the parking recipe reverted, confirming slot-15's suspicion.** Live backlog entry for this task now
reads back `priority: 50` (not the 999 slot-14's `/blocked` got applied), `priority_override: false`, and
`prereqs.prerequisites: []` — read directly off the root clone's `data/config/backlog.yaml` (read-only). Per RULES.md §4
"Park a task", `priority_override: true` is REQUIRED alongside `priority: 999` or the next regen tick reverts it to the
plan-derived value — that's exactly what happened here (the override flag was apparently never set, or didn't survive),
even though the specific regen-drops-prereqs bug this pattern named
(`backlog_regen_drops_handtuned_prereqs_2026_07_12.md`) is already fixed in this checkout's agent-orchestrator history
(`8dd5763` present). So the structural gate still doesn't exist — this is the 10th slot burned on the same prose-only
dependency.

**Also notable (informational, not actionable from this task's scope):** `gcloud compute instances list` for
`central-element-323112` shows ZERO instances matching `features-sports*` / `sports*` name patterns right now (all prior
checks today found 3 RUNNING) — the parent plan's Progress Log shows the compute fleet has been repeatedly relaunched
under different name patterns throughout the day (`-085642/-085703/-085726` → `-002915/-002934/-002956` →
`-000856/-000924/-000944` → GW-recompute `fss-1/2/3`, which self-deleted on completion per the plan's 20:0xZ
autonomous-tick-2 entry) as part of a much larger multi-agent effort (enrichment fleet, ML-loader fixes, odds join-key
fix, all shipped today per the plan's tail). The features `_index/availability_index.parquet` was written 23:32:42Z, ~1
min before this check — fresh consolidator activity, consistent with an active or very-recently-active pipeline, not a
dead one. Whether the 2015→present compute specifically is between relaunch cycles or paused is the parent plan's
concern (already under heavy, current, multi-slot management per its own Progress Log) — out of this todo's scope to
chase or relaunch.

Not re-filing a duplicate `/blocked` (slot-14's structural-gate ask still stands unanswered; a 3rd ask adds no new
information). Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T23:5xZ — data_engineering slot-10 (12th consecutive dispatch — applied main's durable fix from BLK-a1781d76)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep after fresh-pull to LDR HEAD. That plan
currently has exactly 2 open todos: Todo 1 (2015→present compute) and "Features manifest clean over history" (itself
logically downstream of Todo 1).

Found main's answer to slot-2's `/blocked` (`BLK-a1781d76`, answered 23:43:35Z, event id 144301) via the live activity
feed: **B, not A** — the backlog.yaml parking recipe (option A) is rejected as a known-failed action (it reverted twice,
because `PlanRegenLoop` re-derives `backlog.yaml` from the plans every ~30min and a hand-edit not sourced from a plan
gets clobbered). Main's directed **durable fix**: encode the dependency in the SOURCE PLAN itself, the same mechanism
that lets other gates survive regen — read `agent-orchestrator/server/regen_backlog_from_plan.py`
(`_parse_frontmatter_depends_on` / `_parse_frontmatter_gate_on_depends` / `_wire_gate_on_depends_prereqs`, lines
396-461, 1473-1512) to confirm the exact mechanism rather than guess: a plan/issue-doc frontmatter
`depends_on: [<upstream plan filename incl. .md>]` + `gate_on_depends: true` makes every regen tick wire this doc's
derived tasks' `prereqs.completed_tasks` to every currently-open task derived from the named upstream plan(s) — durable
because it's re-derived from the plan file every tick, not a one-off YAML poke. Confirmed the exact frontmatter shape
against a live working example (`deployment_registry_firestore_p4_dynamodb_2026_07_14.md`'s
`depends_on:`/`gate_on_depends: true` block).

**Applied**: added `depends_on: [sports_p2_features_history_to_ml_ready_2026_06_27.md]` + `gate_on_depends: true` to
this issue doc's frontmatter (this doc, above). Since the upstream plan currently has only 2 open todos (both
legitimately prerequisite to a meaningful Todo-2 gap-fill), this should stop the churn without over-gating. This is a
plans-repo frontmatter edit (worker write-scope, NOT the banned root-clone `backlog.yaml` hand-edit) — implements main's
directed fix, not a unilateral infra decision. Declining Todo 2 itself (still genuinely BLOCKED-PREREQ) — no code
touched, Todo 2 checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T00:1x UTC — data_engineering slot-11 (Todo 2 re-dispatch — 13th consecutive check; depends_on fix confirmed committed but not yet wired by regen)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep after fresh-pull to LDR HEAD.

**Checked slot-10's durable fix took effect**: `git log` on this issue doc shows `bab7a2250` (the
`depends_on: [sports_p2_features_history_to_ml_ready_2026_06_27.md]` + `gate_on_depends: true` frontmatter commit)
landed, and it's present in this doc's frontmatter (confirmed by read). But `GET /api/backlog` for this task's entry
shows `priority: 50`, no visible `prereqs.prerequisites`/`completed_tasks` gate, and `dispatch_reason` on my own `/boot`
was "prereqs met" — i.e. the `depends_on`→`prereqs.completed_tasks` wiring hasn't been applied by `PlanRegenLoop` yet
(fix committed only ~20 min before this dispatch; regen ticks ~every 30 min, so this is expected lag, not a failure of
the fix). Separately confirmed the OLD condition-based mechanism (`sports-p2-todo1-2015-present-complete`) is a dead
end, not the live fix: `GET /api/state` shows it exists (`value: false`, `set_by: main`) but `gates_queued: 0` — never
attached to any task, consistent with slot-2's 00:0x finding that only half the parking recipe landed. That mechanism is
superseded by slot-10's `depends_on` fix now in the doc; no further action needed on it.

Cheap non-GCS-walk fleet check (`gcloud compute instances list --project=central-element-323112`, filtered
`sport|features`): **zero** running instances right now — fleet between relaunch cycles, consistent with slot-2's 00:0x
note.

Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task` with reason recorded (per-slot
exclusion so slot-11 isn't redispatched this exact task again while it stays structurally blocked). Recommend the next
dispatch wait for a `PlanRegenLoop` tick (~30 min from `bab7a2250`) before re-checking whether `depends_on` actually
gated this task out of the queue — if it's STILL being dispatched after that window, the `depends_on`/`gate_on_depends`
mechanism itself may not apply to issue-doc-derived tasks the way it does for plan-derived tasks, and that would be a
genuine escalation-worthy finding (not another identical re-check).

### 2026-07-15T00:0x UTC — data_engineering slot-2 (Todo 2 re-dispatch — 11th consecutive check; filed fresh `/blocked`, prior ones had cleared unanswered)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep after fresh-pull to LDR HEAD. Non-snap
`gcloud compute instances list` (`central-element-323112`, filtered `sport|features`): **zero** matching instances
currently running — the backfill fleet is between relaunch cycles right now (consistent with slot-8's 23:3xZ note that
the fleet gets repeatedly relaunched under rotating name patterns); whether that's a stall or a normal gap is the parent
plan's concern, out of this todo's scope. Skipped the full bounded by-date GCS listing this dispatch — it timed out at 2
min on `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=*/` (bucket has grown large enough
that even a prefix-only listing is now expensive); not worth a second attempt given zero VMs are actively writing right
now anyway.

**Checked the live orchestrator state directly** (`GET /api/state`): `blocked_queue` is **empty** — slot-14's original
`/blocked` ask (14:0xZ) is no longer in the queue (answered-and-cleared or expired, not visibly resolved in this doc's
history) but `prerequisites` confirms the exact half-applied state slot-15/slot-8 diagnosed: the condition
`sports-p2-todo1-2015-present-complete` DOES exist (`set_by: "main"`, `set_at: 2026-07-14T13:23:26Z`, `value: false`)
but reads `gates_queued: 0` — meaning it is not attached to ANY task, confirming main created the condition (step 1 of
RULES.md §4's park recipe) but never did the YAML attach (step 2: `prereqs.prerequisites` on this task's `backlog.yaml`
entry) — genuinely a root-clone edit outside worker write scope. Filed a fresh `/blocked` (`BLK-a1781d76`, since the
queue was empty — not a duplicate) spelling out the exact remaining fix for main: attach
`prereqs.prerequisites: [sports-p2-todo1-2015-present-complete]` + `priority: 999` + `priority_override: true` to this
task's backlog entry, `POST /api/backlog/reload`, and verify it survives the next regen tick (it has NOT survived twice
so far). Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-14T23:56 UTC — data_engineering slot-4 (Todo 2 re-dispatch — 14th consecutive check; depends_on fix confirmed committed, regen lag still within expected window)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` via direct grep after fresh-pull to LDR HEAD.

Re-checked slot-10's durable `depends_on` fix (`bab7a2250`,
`depends_on: [sports_p2_features_history_to_ml_ready_2026_06_27.md]` + `gate_on_depends: true`): commit timestamp
`2026-07-14 23:50:19 +0000`, this dispatch's check at `23:56:43 UTC` — only ~6 minutes elapsed. Root-clone
`agent-orchestrator/data/config/backlog.yaml` (read-only check) still shows `prereqs.completed_tasks: []` /
`prereqs.prerequisites: []` on this task's entry, matching slot-11's finding — expected, since `PlanRegenLoop` ticks
~every 30 min and only ~6 min have passed since the fix landed, not yet evidence the mechanism has failed. Skipped a
redundant fleet/coverage GCS check — slot-11 completed one ~6 minutes prior with no reason to expect material drift in
that window (single-walk discipline).

Declining — no action taken, no code touched, checkbox NOT flipped. Recommend the next dispatch (if any) wait until at
least ~30 min post-`bab7a2250` (i.e. after ~00:20 UTC) before treating continued dispatch as evidence the `depends_on`
mechanism doesn't apply to issue-doc-derived tasks. `/skip-current-task`.

### 2026-07-15T00:00 UTC — data_engineering slot-7 (Todo 2 re-dispatch — 15th consecutive check; still inside expected regen-lag window)

**Todo 2 — still BLOCKED-PREREQ, unchanged.** Parent plan `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
("Compute features 2015→present") confirmed still `[ ]` after fresh-pull to LDR HEAD (`434604fae`). Live backlog entry
for this task (`GET /api/backlog`) still shows no `prereqs.completed_tasks`/`prereqs.prerequisites` — `depends_on` fix
(`bab7a2250`, landed 23:50:19Z) is only ~10 min old at this check (00:00:34Z), well inside the ~30 min `PlanRegenLoop`
tick window slot-4 already flagged (wait-until ~00:20Z). Skipped the redundant GCS/fleet re-check — slot-2/slot-4/
slot-11 all checked within the last few minutes with no reason to expect drift (single-walk discipline). No new
information to add beyond slot-4's entry immediately above. Declining — no action taken, no code touched, checkbox NOT
flipped. `/skip-current-task`.

### 2026-07-15T12:3x UTC — data_engineering slot-12 (18th consecutive dispatch — root-caused + fixed why `gate_on_depends` never wired, shipped hotfix)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
after fresh-pull to LDR HEAD — Todo 1's own Progress Log shows it still in-progress as of 10:10Z today. Not attempting
the gap-fill identify/re-run yet — the affected-range boundary genuinely isn't stable until Todo 1 completes.

**But the churn itself was diagnosable, not just re-checkable — root-caused it.** This is dispatch #18 of this exact
task, ~12.5h past slot-10's `bab7a2250` `depends_on`/`gate_on_depends` fix (well past every `PlanRegenLoop` lag window
slot-4/slot-7/slot-11 flagged as "give it 30 min"). Read `agent-orchestrator/server/regen_backlog_from_plan.py` directly
instead of re-polling: `_parse_frontmatter_depends_on()` returns `depends_on` list entries **verbatim**, including a
literal `.md` suffix when written as `depends_on: [upstream_2026_06_27.md]` (exactly the form both this doc's own
frontmatter AND main's cited "confirmed working example" `deployment_registry_firestore_p4_dynamodb_2026_07_14.md` use).
But `_wire_gate_on_depends_prereqs()` matches those entries against `file_to_ids` keys built via `_stem()`, which
**strips** `.md` from every `plan_ref` basename. So `file_to_ids.get(dep, [])` always misses (`"upstream_2026_06_27.md"`
never equals `"upstream_2026_06_27"`), `upstream_ids` stays empty, and the whole wiring pass silently no-ops —
`if not upstream_ids: continue`. Same bug class also affects `_scrub_completed_upstream_prereqs()`'s `_id_slug()`
date-stripping regex (anchored on end-of-string, so a trailing `.md` blocks the date match too). Confirmed empirically,
not just by code-reading: `agent-orchestrator/data/config/backlog.yaml` (root clone, read-only) still reads
`prereqs.completed_tasks: []` for this exact task on a live regen tick that landed mid-investigation — reproduced the
no-op live, in production, not just in theory. The existing test suite (`tests/test_regen_backlog_from_plan.py`) never
caught this because its `_fp_gate()` helper writes `depends_on` WITHOUT the `.md` extension — the bare-stem form that
happens to work; nobody had a test for the `.md`-suffixed form real authors (including main, per slot-10's citation)
actually use.

**Fixed**: `agent-orchestrator@2d6365f` — added `_strip_md_suffix()`, applied at all three return paths in
`_parse_frontmatter_depends_on()` so entries always resolve to bare stems regardless of which form the author wrote.
Added a regression test (`test_regen_gate_on_depends_wires_with_md_suffix`) covering the `.md`-suffixed case. QG green
(1280 passed, ruff/basedpyright clean), shipped via
`quickmerge --agent --files 'server/regen_backlog_from_plan.py tests/test_regen_backlog_from_plan.py'` → landed on
`live-defi-rollout`. This is a hotfix/regression-rescue inline with this task's dispatch (worker.md exception #1) — it
doesn't touch sports/features-service code and doesn't unblock Todo 2 itself (Todo 1 still incomplete), but it fixes the
mechanism so `gate_on_depends` actually gates future dispatches fleet-wide, not just this one task — main directed this
exact mechanism (slot-10's 2026-07-14T23:5xZ entry) as the durable fix for backlog-parking churn generally.

**Not yet verified**: whether the LIVE orchestrator server process (root clone, uvicorn on the `planning` VM) picks up
this fix automatically via its own deploy path, or needs an explicit pull+restart — that's outside a worker's write
scope (root-clone read-only) and outside this task's remit to action. Until the live process runs post-`2d6365f` code,
`Todo 2` (and any other `gate_on_depends`-gated task using the `.md`-suffixed form) will keep dispatching on every regen
tick despite unmet prereqs — recommend main/operator confirm the live process has picked up `2d6365f` (or trigger its
deploy) before assuming the churn has stopped.

Declining Todo 2 itself — no code touched for the sports/features fix, checkbox NOT flipped (still genuinely
BLOCKED-PREREQ). `/skip-current-task`.

### 2026-07-15T13:0xZ — data_engineering slot-5 (19th consecutive dispatch — confirmed the shipped `2d6365f` fix still hasn't taken effect on the LIVE process; filed a fresh, specific `/blocked` asking for a restart/redeploy)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
after fresh-pull to LDR HEAD. No action on the sports/features gap-fill itself — the affected-range boundary still isn't
stable until Todo 1 completes.

**Confirmed the churn is still live, ~30 min after slot-12's `2d6365f` fix landed.** Queried the live backlog directly
(`GET /api/backlog`) for this exact task's record: no `prereqs`/`depends_on` field present at all on the dispatched
record (`status: dispatched`, `dispatched_to: 5`, `queued_at: 2026-07-15T12:41:47Z`) — i.e. this dispatch was queued
~12:41Z, well after `2d6365f` landed (~12:3xZ), so this is not just stale in-flight state from before the fix; the live
regen has run since and STILL isn't wiring `gate_on_depends` for this task. Filed a fresh, narrowly-scoped `/blocked`
question (`BLK-da828631`) distinct from the prior general "why does this keep dispatching" asks — this one specifically
names the already-shipped commit and asks main/operator to confirm+trigger a pull+restart of the LIVE orchestrator
process (root clone), since that action is outside a worker slot's write scope (read-only against root clones) and is
the one concrete thing left standing between the shipped fix and it actually taking effect. Declining this dispatch — no
code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T13:2xZ UTC — data_engineering slot-9 (21st consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (`gcloud compute instances list`, `central-element-323112`, non-snap binary):
`features-sports-sports-20260715-004933` still `RUNNING` — same VM slot-6 observed ~10 min earlier, no crash, no stall.
Skipped the redundant full-corpus GCS date-count walk (single-walk discipline — slot-6 covered fleet state minutes ago).

Re-checked whether the operator-owned `systemctl restart orchestrator.service` (routed by main in response to slot-5's
`BLK-da828631`, per slot-6's note) has landed: `GET /api/backlog` for this task's live dispatched record still shows no
`prereqs.completed_tasks`/`prereqs.prerequisites` field — restart still pending, `gate_on_depends`
(agent-orchestrator@2d6365f) not yet in effect on the live process. Main already answered this exact question and
explicitly said "keep declining cheaply each dispatch ... Tracked — do not re-file" — not filing a duplicate `/blocked`.
Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T13:1xZ UTC — data_engineering slot-6 (20th consecutive dispatch — main answered BLK-da828631, restart routed to operator, no re-file needed)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
after fresh-pull to LDR HEAD (`094756d64`, 2026-07-15 10:11:59Z). Main answered slot-5's `BLK-da828631` at 13:13:25Z (2
min before this check, per live activity feed id 151444): fix `agent-orchestrator@2d6365f` is correct, the remaining
action is a `systemctl restart orchestrator.service` on the planning VM to reload already-pulled code —
operator/backend-owned, main is routing the trigger, and explicitly said "keep declining cheaply each dispatch ...
Tracked — do not re-file." So: not filing a new `/blocked` (would duplicate a just-answered, still-open action item).
Skipped the redundant GCS/fleet re-check — slot-5 checked ~2 min prior with no reason to expect drift (single-walk
discipline); one `features-sports-sports-20260715-004933` VM confirmed `RUNNING` via a cheap non-GCS-walk
`gcloud compute instances list`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-15T13:3xZ UTC — data_engineering slot-13 (22nd consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Root-clone
`agent-orchestrator/data/config/backlog.yaml` (read-only check) for this task's entry still shows
`prereqs.completed_tasks: []` / `prereqs.prerequisites: []` — the `gate_on_depends` fix (`agent-orchestrator@2d6365f`)
still hasn't taken effect on the live process, consistent with slot-9's finding ~2 dispatches ago. Cheap non-GCS-walk
fleet check (non-snap `gcloud compute instances list --project=central-element-323112`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM slot-9 observed) — no crash, no stall. Main already
answered this exact question (routed the restart to the operator, said "keep declining cheaply each dispatch ... Tracked
— do not re-file") — not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT
flipped. `/skip-current-task`.

### 2026-07-15T13:4xZ UTC — data_engineering slot-14 (23rd consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (non-snap `gcloud compute instances list --project=central-element-323112`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM slot-9/slot-13 observed) — no crash, no stall. Skipped
the redundant full-corpus GCS date-count walk (single-walk discipline — no new value this soon after slot-13).

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no
`prereqs.completed_tasks`/`prereqs.prerequisites` field — restart still pending, `gate_on_depends`
(agent-orchestrator@2d6365f) not yet in effect on the live process. Main already answered this exact question and said
"keep declining cheaply each dispatch ... Tracked — do not re-file" — not filing a duplicate `/blocked`. Declining — no
action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T13:5xZ UTC — data_engineering slot-15 (24th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (non-snap `gcloud compute instances list --project=central-element-323112`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM slot-9/slot-13/slot-14 observed) — no crash, no stall.
Skipped the redundant full-corpus GCS date-count walk (single-walk discipline — no new value this soon after slot-14).

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no
`prereqs.completed_tasks`/`prereqs.prerequisites` field — restart still pending, `gate_on_depends`
(agent-orchestrator@2d6365f) not yet in effect on the live process. Also checked `GET /api/state`'s `blocked_queue`
(empty — no new answer to act on) and the live activity feed (last 30 events, no restart/`2d6365f` mention). Main
already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" — not
filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T13:6xZ UTC — data_engineering slot-3 (25th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (non-snap `gcloud compute instances list --project=central-element-323112`, filter `sport|features`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM slot-9/13/14/15 observed) — no crash, no stall.
Skipped the redundant full-corpus GCS date-count walk (single-walk discipline — no new value this soon after slot-15).

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no
`prereqs.completed_tasks`/`prereqs.prerequisites` field — restart still pending, `gate_on_depends`
(agent-orchestrator@2d6365f) not yet in effect on the live process. Checked `GET /api/state`'s `blocked_queue` (empty —
no new operator answer to act on) and the live activity feed (last 15 events: `plan_health_dispatch_initiated`,
`worker_polling_dead`, `slot_idle_stale`, `worker_kicked`, `autospawn_succeeded`, `task_dispatched`,
`idle_blocker_inferred`, `slot_boot` — no restart/`2d6365f` mention). Main already answered this exact question and said
"keep declining cheaply each dispatch ... Tracked — do not re-file" — not filing a duplicate `/blocked`. Declining — no
action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T23:5xZ UTC — data_engineering slot-2 (27th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (non-snap `gcloud compute instances list --project=central-element-323112`, filter `sport|features`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM every predecessor slot since ~13:2xZ has observed) —
no crash, no stall, ~10h uptime on this VM. Skipped the redundant full-corpus GCS date-count walk (single-walk
discipline — no new value this soon after slot-16).

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no `prereqs`/
`depends_on` field — restart still pending, `gate_on_depends` (agent-orchestrator@2d6365f) not yet in effect on the live
process, ~11h after the fix shipped. Main already answered this exact question and said "keep declining cheaply each
dispatch ... Tracked — do not re-file" — not filing a duplicate `/blocked`. Declining — no action taken, no code
touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-15T23:5xZ UTC — data_engineering slot-10 (28th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (`81e360c9c`, all 24 slot repos clean FF-pull, no conflicts). Cheap
non-GCS-walk fleet check (non-snap `gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): `features-sports-sports-20260715-004933` still `RUNNING` (same VM every predecessor slot has observed
since ~13:2xZ, ~30h uptime now) — no crash, no stall.

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no `prereqs`/
`depends_on` field — restart still pending, `gate_on_depends` (agent-orchestrator@2d6365f) not yet in effect on the live
process, now ~11.5h after the fix shipped. `GET /api/state`'s `blocked_queue` is empty — no new operator answer to act
on. Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not
re-file" — not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-15T16:4xZ UTC — data_engineering slot-16 (26th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present") confirmed still `[ ]`
via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts). Cheap non-GCS-walk fleet
check (non-snap `gcloud compute instances list --project=central-element-323112`, filter `sport|features`):
`features-sports-sports-20260715-004933` still `RUNNING` (same VM every predecessor slot has observed since ~13:2xZ) —
no crash, no stall. Skipped the redundant full-corpus GCS date-count walk (single-walk discipline — no new value this
soon after slot-3).

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record still shows no `prereqs`/
`depends_on` field at all — restart still pending, `gate_on_depends` (agent-orchestrator@2d6365f) not yet in effect on
the live process, ~4h after the fix shipped. Checked `GET /api/state`'s `blocked_queue` (empty — no new operator answer
to act on) and the last 15 activity events (`git_status_reported`, `worker_kicked`, `tmux_session_lost`,
`slot_progress`, `worker_polling_dead`, `slot_idle_stale`, `escalation_unresolved`, `unpushed_plans_alert_sent` — no
restart/`2d6365f` mention). Main already answered this exact question and said "keep declining cheaply each dispatch ...
Tracked — do not re-file" — not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox
NOT flipped. `/skip-current-task`.

### 2026-07-16T00:0xZ UTC — data_engineering slot-11 (29th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD. Cheap non-GCS-walk fleet check (non-snap
`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filtered
`sport|features`): `features-sports-sports-20260715-004933` still `RUNNING` (same VM every predecessor slot has observed
since ~13:2xZ 2026-07-15, now >34h uptime) — no crash, no stall.

Re-checked whether the `systemctl restart orchestrator.service` (routed to the operator per main's answer to
`BLK-da828631`) has landed: `GET /api/backlog` for this task's live dispatched record (`dispatched_to: 11`,
`queued_at: 2026-07-15T23:57:04Z`) still shows no `prereqs`/`depends_on` field at all — restart still pending,
`gate_on_depends` (`agent-orchestrator@2d6365f`) not yet in effect on the live process. `GET /api/state` confirms
`server_started: 2026-07-15T07:30:19Z` — the live uvicorn process predates the fix by ~5h, direct evidence no restart
has occurred since. `blocked_queue` is empty (no new operator answer to act on). Main already answered this exact
question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" — not filing a duplicate
`/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-16T00:1xZ UTC — data_engineering slot-7 (30th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD. Cheap non-snap fleet check
(`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): `features-sports-sports-20260715-004933` still `RUNNING` (same VM every predecessor slot has observed
since ~13:2xZ 2026-07-15) — no crash, no stall.

Re-checked whether the `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from slot-11's check, restart still pending, `gate_on_depends`
(`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~12h post-fix). Root-clone `backlog.yaml`
entry for this task confirms `prereqs.completed_tasks: []` / `prereqs.prerequisites: []` still unwired. `blocked_queue`
empty — no new operator answer. Main already answered this exact question and said "keep declining cheaply each dispatch
... Tracked — do not re-file" — not filing a duplicate `/blocked`. Declining — no action taken, no code touched,
checkbox NOT flipped. `/skip-current-task`.

### 2026-07-16T00:4xZ UTC — data_engineering slot-12 (31st consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD (all 24 slot repos clean FF-pull, no conflicts).

Re-checked whether `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from slot-7's check, restart still pending, `gate_on_depends`
(`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~12.5h post-fix). Live `GET /api/backlog`
entry for this exact task confirms no `prereqs`/`depends_on` field at all on the dispatched record. `blocked_queue`
empty — no new operator answer to act on.

Cheap non-GCS-walk fleet check
(`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): **zero** matching instances running right now — `features-sports-sports-20260715-004933` (the VM
every predecessor slot since ~13:2xZ 2026-07-15 observed RUNNING) is gone. Informational only, consistent with
slot-2's/slot-8's 2026-07-14/15 notes that this fleet gets repeatedly relaunched under rotating name patterns between
passes — whether this is a between-cycles gap or a stall is the parent plan's concern, out of this todo's scope to
chase.

Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" —
not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-16T12:5xZ UTC — data_engineering slot-5 (32nd consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD (all 25 slot repos clean FF-pull, no conflicts).

Re-checked whether `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from every prior check since slot-11's 2026-07-16T00:0xZ finding,
restart still pending, `gate_on_depends` (`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~24h
post-fix). Live `GET /api/backlog` entry for this exact task (`dispatched_to: 5`, `queued_at: 2026-07-16T12:49:35Z`)
confirms no `prereqs`/`depends_on` field at all on the dispatched record. `blocked_queue` empty — no new operator answer
to act on.

Cheap non-GCS-walk fleet check
(`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): **zero** matching instances running right now — consistent with slot-12's prior observation of the
fleet between relaunch cycles; whether this is a stall or a normal gap remains the parent plan's concern, out of this
todo's scope to chase.

Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" —
not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-16T13:2xZ UTC — data_engineering slot-6 (33rd consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD (`1c8597a5b`).

Re-checked whether `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from every prior check since slot-11's 2026-07-16T00:0xZ finding,
restart still pending, `gate_on_depends` (`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~30h
post-fix). Live `GET /api/backlog` entry for this exact task (`dispatched_to: 6`, `queued_at: 2026-07-16T13:18:39Z`)
confirms no `prereqs`/`depends_on` field at all on the dispatched record. `blocked_queue` empty — no new operator answer
to act on.

Cheap non-GCS-walk fleet check
(`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): **zero** matching instances running right now — consistent with slot-12's/slot-5's prior observations
of the fleet between relaunch cycles; whether this is a stall or a normal gap remains the parent plan's concern, out of
this todo's scope to chase.

Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" —
not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-16T13:3xZ UTC — data_engineering slot-3 (34th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD.

Re-checked whether `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from every prior check since slot-11's 2026-07-16T00:0xZ finding,
restart still pending, `gate_on_depends` (`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~30h
post-fix). Live `GET /api/backlog` entry for this exact task (`dispatched_to: 3`, `queued_at: 2026-07-16T13:25:39Z`)
confirms no `prereqs`/`depends_on` field at all on the dispatched record. `blocked_queue` empty — no new operator answer
to act on.

Cheap non-GCS-walk fleet check
(`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): **zero** matching instances running right now — consistent with slot-6's/slot-5's prior observations
of the fleet between relaunch cycles; whether this is a stall or a normal gap remains the parent plan's concern, out of
this todo's scope to chase.

Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" —
not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-16T14:3xZ UTC — data_engineering slot-9 (35th consecutive dispatch — restart still pending, no re-file per main's standing answer)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `[ ]` via direct grep after fresh-pull to LDR HEAD (`67f35e579`, all 24 slot repos clean FF-pull, no conflicts).

Re-checked whether `systemctl restart orchestrator.service` has landed: `GET /api/state` still shows
`server_started: 2026-07-15T07:30:19Z` — unchanged from every prior check since slot-11's 2026-07-16T00:0xZ finding,
restart still pending, `gate_on_depends` (`agent-orchestrator@2d6365f`) not yet in effect on the live process (now ~31h
post-fix). Live `GET /api/backlog` entry for this exact task (`dispatched_to: 9`, `queued_at: 2026-07-16T13:42:32Z`)
confirms no `prereqs`/`depends_on` field at all on the dispatched record. `blocked_queue` empty — no new operator answer
to act on.

Main already answered this exact question and said "keep declining cheaply each dispatch ... Tracked — do not re-file" —
not filing a duplicate `/blocked`. Declining — no action taken, no code touched, checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-16T18:2xZ UTC — data_engineering slot-13 (36th consecutive dispatch — restart FINALLY landed, but surfaced a new bug: `gate_on_depends` is now live and trusting a FALSE prereq-done state)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) and the
"Features manifest clean over history" todo (line 109) both confirmed still `- [ ]` via direct grep after a clean
fresh-pull to LDR HEAD `9d39ed2835ae` (2026-07-16T18:21:16Z, all 25 slot repos clean FF-pull, no conflicts).

**The long-awaited restart has landed.** `GET /api/state` now shows `server_started: 2026-07-16T18:21:11Z` — the first
change from `2026-07-15T07:30:19Z` since slot-11 first flagged the stale process at 2026-07-16T00:0xZ (~30 consecutive
checks ago). `agent-orchestrator@2d6365f` (`gate_on_depends`'s `.md`-suffix fix) is finally in effect: this task's live
backlog entry now carries
`prereqs.completed_tasks: [sports_p2_features_history_to_ml_ready-001, sports_p2_features_history_to_ml_ready-002]`
(previously always empty), and my own `/boot` dispatched with `dispatch_reason: "... prereqs met ..."` instead of the
historical "no gate applied" reason.

**But the gate is trusting a FALSE completion state.** Both prereq tasks read `status: done` via `GET /api/backlog` —
`sports_p2_features_history_to_ml_ready-001` with `done_sha: 094756d64`, `-002` with `done_sha: 0402f7a86`. Checked both
SHAs: `094756d64` is a "Todo 1 re-verify — ... no new action needed (slot-11)" decline commit; `0402f7a86` is a "Todo 3
re-verify — still BLOCKED-PREREQ (slot-8)" decline commit for a different todo entirely. Neither is a completion commit,
and — as this doc's own 30+ prior entries already established beyond doubt — the actual plan checkboxes for both source
todos remain unflipped. So `gate_on_depends` just dispatched this task on a **false** "prereqs met" signal: the
mechanism finally works, but the data it's trusting is wrong.

**Filed a new issue doc** (not a duplicate of this one — this is a distinct, orchestrator-internal data-integrity bug,
not a sports/features-service concern):
`plans/active/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`, `assigned_role: infra`, with 2
P1 root-cause/fix todos + 1 P2 todo to re-verify this exact gate once fixed. This is a "big finding" (cross-cutting SSOT
contradiction between backlog `status` and the plan checkbox codex/ CLAUDE.md declare authoritative) per the
findings-triage HARD RULE — filed rather than silently declining, since the false-positive risk isn't scoped to just
this one task.

**Todo 2 itself remains genuinely premature** — ground truth (the plan checkbox + this plan's own Progress Log, still
~68%+ coverage not 100%) is unchanged regardless of the backlog's incorrect `done` marking; the affected-range boundary
still isn't stable until the real 2015→present compute finishes. Declining — no sports/features code touched, Todo 2
checkbox NOT flipped. `/skip-current-task`.

### 2026-07-16T18:5xZ UTC — data_engineering slot-16 (38th consecutive dispatch — server restarted again since slot-14's check, but false-gate SHAs + ground truth both unchanged)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `- [ ]` via direct grep after a clean fresh-pull to LDR HEAD (all 25 slot repos clean FF-pull, no conflicts).

**Noted a new server restart** — `GET /api/state` now shows `server_started: 2026-07-16T18:45:24Z`, later than the
`2026-07-16T18:21:11Z` slot-13/slot-14 observed. Checked whether this restart shipped the infra issue doc's P1 hard-409
fix (`plans/active/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`): grepped
`agent-orchestrator/server/routes/slots_worker.py` directly — `no_plan_flip` is still only a non-blocking `DoneWarning`
(lines ~712/870/883), no hard-409 path added; that issue doc's 2nd P1 todo (upgrade to hard-409) and P2 audit-sweep todo
are both still `[ ]` unassigned. So this restart is unrelated to that fix (routine respawn, not a fix deploy).

Re-checked the false-gate prereqs directly (`GET /api/backlog` for `sports_p2_features_history_to_ml_ready-001`/`-002`):
both still `status: done` with the identical stale `done_sha`s (`094756d64` / `0402f7a86`) slot-13/14 already
root-caused as decline-commits, not completions — unchanged since first observed. Ground truth (this plan's own Todo 1
checkbox, line 101) contradicts it, same as every one of the last 30+ checks. Not filing a duplicate issue doc or
`/blocked` — the infra issue doc already tracks the fix + audit-sweep todos; this dispatch adds no new information
beyond confirming both are still open. Declining — no sports/features code touched, Todo 2 checkbox NOT flipped.
`/skip-current-task`.

### 2026-07-17T12:xxZ UTC — data_engineering slot-4 (39th consecutive dispatch — Todo 1 GENUINELY complete, real Todo 2 work done, verified no gap-fill needed, new issue doc filed)

**Todo 1 confirmed genuinely complete** (not the false-gate bug flagged by slot-13/14/16): parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` line 118 now reads `[x] ✅` with evidence "10-VM
`fss-backfill-vm-1..10` fleet (2015-01-01→2026-07-17) all exited rc=0 and self-deleted... 4216/4216 dates fully complete
(100.0%)". Confirmed via `git log -1`: HEAD is exactly commit `273a7a059` ("docs(plans): flip Todo 1 — sports features
2015→present compute complete (4216/4216, 100.0%)"), fresh-pulled to `origin/live-defi-rollout` HEAD (`5d3f7b363`), all
25 slot repos clean. This is real, not the `agent-orchestrator@2d6365f`-related false-`done` bug slot-13/14/16 found on
the backlog's own status field (that bug was about the BACKLOG task's `status`, not this plan's actual checkbox — the
checkbox itself is genuinely flipped with real evidence).

**Did the actual Todo 2 work** (identify + gap-fill). Read the sports features availability manifest
(`gs://features-sports-prd-central-element-323112/_index/availability_index.parquet`, single file, one-time read — not a
whole-corpus GCS walk) to find `DERIVED_FEATURES`/`captured` shards written before the fix (`features-service@d878f11a`,
2026-07-14T12:20:33Z): 24,285 rows / 1,845 unique dates pre-fix. Rather than blast a --force re-run across all 1,845
dates unverified, content-sampled real parquet data first (craft north-star #2: minimum work to move the data correctly)
— three samples, 7,641 rows total, spanning a broad 2017-2026 stratified sample, the EXACT 111-date/1,558-shard window
matching the documented 08:56-12:20:33Z crash window (GCS `ls -l` mtimes cross-verified directly against the manifest),
and the freshest live day (2026-07-16). **Result: zero rows anywhere show the tz-crash's specific all-5-columns-NaN
pattern.** So Todo 2's originally-recommended action (gap-fill re-run scoped to all-NaN dates) has nothing to act on —
verified negative, not another decline-for-prereq-reasons.

**Found a different, bigger, still-live defect instead** while sampling: `home_travel_distance_km` NaN in ~100% of rows,
`away_travel_distance_km` NaN in 86-98.5%, and ALL 5 cumulative-travel columns hardcoded to exactly `0.0` (never NaN,
never nonzero) in every one of the 7,641 rows checked — including the freshest live day, computed with today's
fully-patched code. This is unrelated to the tz-crash (traced the mechanism to `_get_team_home_venue_coords` failing to
resolve venue coordinates almost universally, not the tz exception path) and is NOT something to absorb into this issue
doc's scope. Filed as its own issue doc:
`plans/active/issues/sports_travel_calculator_home_venue_coords_never_resolved_2026_07_17.md` (P1, 3 todos, root-cause
lead + fix + re-verify). Flipped Todo 2 `[x]` above with this evidence. `/done`.

### 2026-07-16T18:4xZ UTC — data_engineering slot-14 (37th consecutive dispatch — false-gate dispatch confirmed again, ground truth unchanged, no re-file)

**Todo 2 — still BLOCKED-PREREQ, unchanged (genuinely).** Parent plan
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 ("Compute features 2015→present", line 101) confirmed
still `- [ ]` via direct grep after fresh-pull to LDR HEAD (all 25 slot repos clean FF-pull, no conflicts).

Re-confirmed slot-13's finding from the immediately-prior dispatch: `GET /api/backlog` for this exact task
(`dispatched_to: 14`, `queued_at: 2026-07-16T18:37:23Z`) shows `dispatch_reason` gated on
`prereqs.completed_tasks: [sports_p2_features_history_to_ml_ready-001, sports_p2_features_history_to_ml_ready-002]` both
marked `status: done` — but those `done_sha`s (`094756d64` / `0402f7a86`) are decline commits, not completion commits,
and the actual plan checkbox (line 101) is still unflipped. So `gate_on_depends` (agent-orchestrator@2d6365f) is
dispatching on a false "prereqs met" signal, exactly as slot-13 documented. Slot-13's issue doc
(`plans/active/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`, `assigned_role: infra`, 2
P1 + 1 P2 todos) already tracks this — not filing a duplicate.

Cheap non-GCS-walk fleet check (`gcloud compute instances list --project=central-element-323112`, filter
`sport|features`): **zero** matching instances running right now — consistent with the last several checks of the fleet
between relaunch cycles; whether this is a stall or a normal gap remains the parent plan's concern, out of this todo's
scope to chase.

Ground truth is unchanged: the affected-range boundary for this todo's gap-fill still isn't stable until Todo 1's real
2015→present compute completes. Declining — no sports/features code touched, Todo 2 checkbox NOT flipped.
`/skip-current-task`.
