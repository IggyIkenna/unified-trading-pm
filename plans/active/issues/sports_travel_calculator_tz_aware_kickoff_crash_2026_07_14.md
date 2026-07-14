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
status: open
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
last_updated: 2026-07-14
locked_by:
resolved_by:
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
- [ ] [DATA] P2. **After `sports_p2_features_history_to_ml_ready-002` Todo 1 (2015→present compute) reaches
      completion**, identify date-ranges computed BEFORE features-service@d878f11a landed (2026-07-14) whose
      `sports_features/by_date/day=*/feature_group=*` cumulative-travel columns
      (`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`*_travel_per_game_30d`/`travel_fatigue_ratio`) are
      suspiciously all-NaN for dates with tz-aware `kickoff_utc` fixtures, and gap-fill re-run those with `--force` on
      the fixed code. (repo: features-service)
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
