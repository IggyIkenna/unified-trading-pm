---
doc_type: plan
title: Code readiness T5 — readiness derivation, observability and the presentation artefacts
summary: >-
  Tranche 5 of the five-agent code-readiness push — owns the derived readiness state itself, honest-coverage reporting, observability and alerting, and the four client artefacts that are this whole effort's acceptance test. Also absorbs the workspace tooling tail once the readiness spine is closed.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, alerting-service, e2e-testing, system-integration-tests, unified-trading-ci, agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [code-readiness, readiness-derivation, honest-coverage, observability, presentations, w21, tranche-5]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 55
estimate_calibrated_ai_days: 22
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel agents and drive the four
  client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: infra
effort: max # multi-day autonomous tranche — 30-40 todos spanning several repos, cross-tranche contract edges
drift_direction: advance-code
---

# Code readiness T5 — readiness derivation, observability and the presentation artefacts

> **Tranche 5 of 5.** Owned repos — **deployment-service, alerting-service, e2e-testing, system-integration-tests, unified-trading-ci, agent-orchestrator, unified-trading-pm**. Allocated corpus —
> **433 docs** (19 spine, 13 excluded as data-movement), **1180 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**You own the acceptance test.** The four artefacts are re-derived by this tranche, and the effort is done
when they stop carrying `pending` / `planned` / `partial` / `not built` / `unverified` on anything outside the five
allowed states. Two hard dependencies gate your headline numbers — T4's execution-instruction check (the structural
reason all 864 rows read `unverified`) and T2's `instrument_type` / `data_type` coverage axes. **Build everything
else first and keep the dump honest meanwhile**: a leg with no real check prints `unverified`, never a silent pass
(operator ruling 2026-08-16).

Your allocation is the largest (433 docs) but only 19 are spine. The rest is AO / CI / plan-hygiene tooling that
does not make the artefacts code-ready — work the spine to done FIRST, then the tail.

## The goalpost — what "done" means (operator ruling 2026-08-19)

Everything in this tranche is **complete in code**. The ONLY things that may still be pending when this plan closes:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK. SSOT for the goalpost:
`/plans/epics/system_readiness_master.md` § "Definition of done".

**The acceptance test is the artefacts.** These four client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html`

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in
`/plans/epics/system_readiness_master.md`. Closing a W-item is what clears its marker. **Never clear a marker by
editing the HTML** — the marker is derived from real state; change the state, then re-derive.

## Standing rules for this tranche — HARD

- **Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes** (operator ruling 2026-08-19). Fixing
  the manifest-writer / path-registry / capture-status **code** is IN scope; launching the data movement is NOT.
  A todo whose only remaining step is "relaunch the VM" or "apply the delete" is marked `BLOCKED-OPERATOR` and left.
- **Do NOT request or wait on API keys / credentials.** Where a real credential is missing, build the adapter and
  the full code path anyway and mark the item `BLOCKED-CREDENTIALS` — never descope it. SSOT:
  `/codex/02-data/external-data-always-available-rule.md`.
- **Edit ONLY the repos this tranche owns** (listed above). Another tranche owns every other repo, and a same-file
  edit across two agents is the one thing the workspace concurrency model forbids. Need a change in someone else's
  repo? File it via the handoff protocol below — never reach across.
- **Every claim ≤ its measurement.** A proxy (line count, exit 0, a green test, a cached `origin/`) is not the
  property. Measure it or say you did not. SSOT: `/codex/12-agent-workflow/measurement-claims-discipline.md`.
- **Commit + push + flip the checkbox in the SAME turn**, with `<repo>@<sha>` evidence. SSOT:
  `/codex/12-agent-workflow/commit-push-flip-rule.md`.
- **Ship code only via** `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` from a `quality-gates.sh`-green
  tree. Doc/plan-only changes go via `bash scripts/dev/safe-doc-push.sh`.

## Cross-tranche handoff protocol

Five agents run in parallel on disjoint repos. When your work needs a change in a repo you do not own:

1. Append a `- [ ]` todo to the OWNING tranche's plan under its `## Inbound requests` section, tagged
   `[FROM-<your-tranche>]`, naming the exact symbol/file and what shape you need.
2. Commit that plan edit via `safe-doc-push.sh` (doc-only, no code).
3. Keep working — build your side against the contract you asked for, behind a feature flag or an adapter seam if
   it does not exist yet. Do not block, and do not edit their repo yourself.

**Known blocking edges at authoring time** (T1 is upstream of everyone — it runs first and fastest by design):

- T4 delta-proxy repricer generalization → needs T1 to extend UAC `QuoteInstruction` with
  `delta` / `gamma` / `underlying_instrument_id`.
- T3 + T4 strategy→execution reference triple → needs T1 to add `reference_position` and `credit` to
  `StrategyInstructionEnvelope`.
- T5 readiness dump's execution-instruction leg (the structural reason all 864 rows read `unverified`) → needs T4
  to expose a real per-venue instruction-path check.
- T5 coverage dump at `instrument_type` / `data_type` grain → needs T2 to land those axes in `coverage.json`.

## Your allocated corpus

The full, reproducible allocation lives in `/plans/audit/results/code_readiness_allocation_2026_08_19.json`,
regenerated by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`. Every one of the 892 active plan/issue
docs is assigned to exactly one tranche, so nothing is orphaned and nothing is worked twice.

```bash
python3 -c "
import json
d=json.load(open('plans/audit/results/code_readiness_allocation_2026_08_19.json'))
for x in d['tranches']['T5-readiness-observability-presentations']['docs']:
    if not x['excluded_data_movement']:
        print(('SPINE ' if x['spine'] else '      '), x['priority'], x['open_todos'], x['path'])
"
```

**Work order**: `spine: true` docs FIRST, in priority order — those are the docs that back a presentation claim.
Then the tail. A doc flagged `excluded_data_movement: true` is skipped per the standing rules above; open its
todos only to confirm they are data-movement, then leave it.

## Inbound requests

> Other tranches append `- [ ] [FROM-Tn]` items here when they need a change in a repo you own. Work them at the
> priority they state — another agent is blocked on each one.

- [ ] [FROM-T1] P1. **Regenerate `platform-external-api-walkthrough.html`'s API-surface enumeration from shipped
      routes** — T1 re-triaged its own plan's "External API surface" section 2026-08-20; the artefact currently
      leaves this "pending, to be enumerated exactly." Spans `instruments-service` + `market-tick-data-service`
      (T2-owned) and `execution-service` (T4-owned) routers — T1 doesn't own any of them, but this is read-only
      route enumeration + doc regeneration, not an edit to those repos, so ownership doesn't block whoever does it
      from reading them directly, the way T5 already does for the readiness dump
      (`cursor-configs/skills/readiness-state-dump/scripts/instruction_actions.py`). Coordinate with T2/T4 only if
      their routers are genuinely mid-change when you walk them.
- [x] [FROM-T3] P0. Fix the two `scripts/quickmerge.sh` defects measured 2026-08-20 across five real ship
      attempts: (1) a FAILED re-gate still exits 0 — three attempts reported success and landed nothing; (2) a
      DIRECTORY path in `--files` stages nothing for it silently, which landed a PARTIAL commit that broke
      `live-defi-rollout` (factory.py referencing an unstaged package). Full measurement, the five-check table
      showing why `git diff FETCH_HEAD` also came back clean during the broken window, and the proposed fixes:
      `/plans/active/issues/quickmerge_exit_zero_on_failed_regate_and_silent_directory_files_2026_08_20.md`.
      P0 because every agent is required to ship through this path and the failure mode is false progress.
      **Defect 2 (directory silently dropped) fixed 2026-08-20**: `unified-trading-pm@d0e5a67ee7` — `--files`
      now refuses any directory path outright (exit 1, before any staging), live-tested against a real throwaway
      directory. **Defect 1 (exit-0-on-failed-regate) investigated, not confirmed as a live code defect**: the
      specific agent-mode re-gate path already propagates its real exit code correctly
      (`${PIPESTATUS[0]}` + unconditional `exit 1`, verified by direct read); the "exited with code 0" evidence in
      both T3's measurement and this session's own repeated observation is fully explained by the near-universal
      `| tee LOG | tail -N` logging convention, which returns `tail`'s exit status, not the piped command's
      (confirmed live: `false | tee x | tail -5; echo $?` → `0`) — left this one open rather than closing on
      unconfirmed evidence; a re-measurement using `${PIPESTATUS[0]}` directly (no `| tail`) is needed before
      concluding whether a further fix is warranted. Also shipped: the recommended per-tab-worktrees.md doc
      addition (`unified-trading-pm@c1d75e7dd7`).
- [x] [FROM-T3] P1. Create `clients.yaml` **or** `clients_waiver.yaml` under
      `deployment-service/configs/strategy/<archetype_lowercase>/` for the 27 archetypes T3 registered on
      2026-08-19 (18 `VOL_*`, 5 granular `MARKET_MAKING_*`, 4 `PORTFOLIO_*`). strategy-service's
      `clients_yaml_coverage.py` gate requires one or the other for every factory-registered archetype;
      T3 cannot create them because `deployment-service` is a T5 repo. The exact 27 values are listed in
      `strategy_service/engine/strategies/v2/clients_yaml_coverage.py`'s `PENDING_CROSS_REPO_WAIVER`
      frozenset — T3 deletes each entry from that set as its file lands, so the set doubles as the
      shrinking worklist. A waiver is the expected answer for most of them (they are seed-only slots with
      no client allocation yet); a `clients.yaml` is only needed where a client actually subscribes.
      **Done 2026-08-20**: all 27 got `clients_waiver.yaml` (none have real client subscriptions yet, matching
      the doc's own framing) — `deployment-service@6d2a0a6028`, verified per-file against origin (27/27) AND by
      running the actual consumer live: `strategy_service.engine.strategies.v2.clients_yaml_coverage
      .uncovered_archetypes()` now returns `[]` (was reporting all 27 as violations before). T3's own
      `PENDING_CROSS_REPO_WAIVER` frozenset in strategy-service is theirs to shrink — not touched here, per
      "edit ONLY the repos this tranche owns"; they'll see it's safe to delete on their next pass since the gate
      itself is now clean independent of that set.

- [x] [FROM-T2] P0. **You are NOT blocked on the coverage grain — it already landed. Re-run the dump.** Your
      "re-run at the finer grain the moment T2 lands `instrument_type` / `data_type`" todo below is waiting on
      something that is already true in production, so the wait is the only thing left to remove. MEASURED
      2026-08-19 by reading the live artefact through your own engine
      (`cursor-configs/skills/honest-coverage-dump/scripts/shard_universe.py`), not by inspecting the writer:

      - `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` (`schema_version: 2`) carries BOTH
        `by_venue_instrument_type` (172 `(ag, venue)` pairs) and `by_venue_instrument_type_data_type` (184 pairs),
        populated for all 5 asset_groups.
      - `detect_grain(payload)` returns **`"instrument_type"`**, and `iter_shard_cells()` yields **3,962** cells at
        `(asset_group, venue, instrument_type, data_type)` grain.
      - Your auto-detect works as documented — you asked to verify rather than assume, so: verified, by executing
        it. No code change was needed on either side for the axes themselves.

      **Two caveats you must carry into the re-run, or the finer grain will report inflated numbers.** Both are
      defects in T2's writer measured the same day, both now fixed in `instruments-service`
      `scripts/measure_honest_coverage.py` (see this tranche's T2 plan Progress Log for the `<repo>@<sha>`) — but
      the fix only reaches the artefact on the NEXT nightly `measure-honest-coverage` cron run, so any dump taken
      against a coverage.json dated on or before 2026-08-19 still contains them:

      1. **The 3,962 cell count is inflated by 86 duplicate cells (2.2%).** 24 `(ag, venue, instrument_type)`
         groups carried two case-variant keys at level 5 (e.g. `sports/LADBROKES` holding both `'ODDS'` with
         `data_types=['trades']` and `'odds'` with `data_types=['odds']` — one shard, two keys); 26 literal
         `'nan'` instrument_type keys sat beside 85 blank ones; and 6 `data_type` groups differed only by case.
         Collapsing all three artifacts gives **3,876** true distinct shards. Quote 3,876, not 3,962 — and state
         the date and denominator beside it either way.
      2. **The `instrument_type` axis is ~50% hollow and the grain label does not say so.** 1,973 of 3,962 cells
         (49.8%) carry a blank or `'nan'` instrument_type, yet `detect_grain()` reports the finer grain for the
         whole payload. Per asset_group: `defi` 1,871/2,804 (66.7%), `tradfi` 82/244 (33.6%), `prediction`
         10/19 (52.6%), `sports` 10/822 (1.2%), `cefi` 0/73 (0%). A reader trusting the label alone believes it
         has a finer breakdown than exists for half the corpus — the same failure mode as the mislabelled `grain`
         field in `readiness_pipeline_stage_per_shard_2026_08_18.json` (next item). Report grain per asset_group,
         or report the hollow fraction beside the label.

      **Done properly, 2026-08-20**: both caveats resolved as durable tool fixes, not a one-off manual report —
      `unified-trading-pm@bb81afbcaa` added `compute_dedup_stats()` to `shard_universe.py` + a `dedup_stats`
      report block to `dump_coverage.py` (distinct-shard count after collapsing case-variant/nan-vs-blank keys,
      plus per-asset-group hollow-instrument_type fraction). Re-measured against 2026-08-20's coverage.json (a
      day newer than T2's 2026-08-19 measurement — the writer fix had NOT self-corrected the existing artefact by
      the next cron run): raw 3965 / distinct **3877** / 88 duplicates collapsed; hollow fractions per asset_group
      `cefi 0/73 (0%) defi 1888/2807 (67.3%) prediction 11/19 (57.9%) sports 18/822 (2.2%) tradfi 145/244
      (59.4%)`. Every future `dump_coverage.py` run now reports both automatically — this does not need re-doing
      by hand again.

- [x] [FROM-T2] P1. **Your readiness dump's `grain` field is mislabelled — the writer, not the file.** This is the
      `/plans/epics/system_readiness_master.md` § W3 `[DOC] P1` item, and it lands in a file this tranche owns, so
      T2 has not touched it. MEASURED: `plans/audit/results/readiness_pipeline_stage_per_shard_2026_08_18.json`
      declares top-level `grain: "instrument_type"` while all 864 rows carry only
      `['venue', 'asset_group', 'mode', 'pipeline_stage', 'leg_states']` — no `instrument_type` key on any row.
      Root cause is in `cursor-configs/skills/readiness-state-dump/scripts/derive_readiness.py:208`:
      `grain = detect_grain(coverage_payload)` reads the grain of the **coverage source** and then reports it as
      the grain of the **readiness rows**, which are built at `venue x asset_group x mode`. The two are different
      things. Suggested shape: emit `row_grain: "venue_asset_group_mode"` for what the rows actually are, and keep
      the source's grain under its own key (`coverage_source_grain`), so neither is silently claiming the other.
      **Fixed exactly per T2's suggested shape, 2026-08-20**: `unified-trading-pm@065067f345`. Verified end-to-end
      (both human-readable and `--json` output paths) against a live dump: header now prints
      `rows: venue_asset_group_mode, coverage source: instrument_type`; JSON carries `row_grain` +
      `coverage_source_grain`, the old ambiguous `grain` key is gone (0 occurrences). The 9-blank-venue-row note
      in this same item is T2's own separate tracking, not touched here.
      Also worth a look while you are in there: 9 rows carry an EMPTY `venue` string (all `asset_group: sports`) —
      they come straight through from 9 blank-venue cells in coverage.json, which T2 is tracking separately.

- [x] [FROM-T4] P0. **The per-venue execution-instruction-path check you are blocked on is BUILT — here is its
      frozen contract, so you can write the probe now rather than waiting.** It is in execution-service (gating
      under quickmerge as of 2026-08-20; T4's plan Progress Log carries the landing `<repo>@<sha>`).

      Call it exactly like the strategy-position probe — a subprocess into execution-service's own venv, never an
      import (tier rule). The entry point already exists, so you do not need to write a probe script body:

      ```bash
      echo '["OKX-FUTURES","AAVE-V3-ETHEREUM"]' | execution-service/.venv/bin/python -m execution_service.readiness
      ```

      stdin: JSON list of canonical dash-form venue names. stdout: `{venue: record}` where record is

      ```json
      {"batch": "none|wired|deployed", "paper": "...", "live": "...",
       "actions": ["TRADE", "CANCEL"], "handlers": ["ManualOperationHandler.execute -> ..."],
       "batch_unhandled_actions": [], "detail": "..."}
      ```

      Importable equivalents if you prefer: `execution_service.readiness.instruction_path_availability(venue)`
      (returns a frozen dataclass) and `...instruction_path_availability_map(venues)`. It performs NO I/O and
      never constructs a live adapter, so it is safe to batch over all 288 venues in one subprocess call.

      Suggested mapping for `checks.py::execution_instruction()`, which today returns a hard-coded `unverified`:
      `"none"` → `not_ready` (no instruction naming this venue reaches any handler — a real negative, not an
      unknown); `"deployed"` → `ready`; `"wired"` → `unverified`, quoting `batch_unhandled_actions` in the reason.
      Note the check is deliberately about ROUTING only — credentials and real venue reachability stay on the
      `execution_orders` leg, so wiring this in does not double-count them.

      Also worth surfacing in the dump: the check measured that `resolve_settlement` has NO batch settlement
      handler for `CONVERT_DUST, LP_BURN, LP_MINT, REPAY, WITHDRAW`, which is why every lending venue derives
      `batch=wired` rather than `deployed`.

## Todos

- [ ] [AGENT] P0. Execute the presentation cluster of the 2026-08-21 walkthrough feedback, tracked in
      `/plans/active/walkthrough_feedback_remediation_2026_08_21.md` (moved: line cap).

### W1 — readiness derivation and the state dump

- [x] [BACKEND] P0. Derive a batch / paper / live state for EVERY venue with a code path, surfacing `unverified`
      honestly wherever a check does not exist. Epic definition-of-done item. Engine:
      `cursor-configs/skills/readiness-state-dump/`. **All 14 legs now do exactly this** — every one either
      derives a real per-venue verdict or reports `unverified` with a specific reason, never a silent pass; the
      MANUAL-mode addition below closed the last gap by surfacing this same discipline for a 4th mode, not just
      the original 3.
- [x] [BACKEND] P0. Wire T4's per-venue execution-instruction check into the dump the moment it lands — this is what
      moves 844 `not_ready` rows off their structural blocker. Track the dependency; do not wait idle on it.
      **2026-08-20 — dependency tracked and the non-blocked half DONE, `unified-trading-pm@c3a3e870f4`.** Request
      filed on T4's `## Inbound requests` naming the exact probe shape (`unified-trading-pm@241933d56e`), with the
      groundwork pre-done so T4 need not re-derive it. Our side: `instruction_actions.py` measures handler coverage
      by AST (11/16 actions have a settlement path; 5 raise `UnhandledActionError`), the leg now carries a measured
      denominator instead of "no check wired", and the SKILL.md pointer that named the WRONG file
      (`v2/policy_resolver.py` — an algo resolver keyed by `(client_id, slot_label)`, not an instruction registry)
      is corrected. Remaining work here is a one-line probe call once T4 lands the venue-aware surface.
      **DONE, `unified-trading-pm@8d47cf3393`** (the cross-venv `_execution_instruction_path_probe.py` +
      `derive_readiness.py` wiring, landed earlier this session — verified by re-running the live dump fresh
      2026-08-20: `execution_instruction` now reports `ready=238 not_ready=600 unverified=26` (real per-venue
      variance) instead of a uniform hardcoded `unverified` across all 864 rows. Confirms the earlier coordinator
      correction still holds: `strategy` (`ready=24 not_ready=840`) remains the dominant structural blocker on the
      overall rollup, not `execution_instruction` — this leg's wiring is real but was never the critical path.
- [x] [BACKEND] P0. Add the archetype capability axis across batch, paper and live to the dump. The artefacts mark
      it `planned — specified and not yet built`, so that axis reports `unverified` today. Consume T3's
      `/archetype-code-completeness` output rather than re-deriving it. **Done** (earlier this session):
      `checks.strategy_archetype_code_complete()` wired as the `strategy_archetype_code` leg in
      `derive_readiness.py:420`, consuming `/archetype-code-completeness`'s output. Re-confirmed live 2026-08-20:
      present with real counts (`ready=360 not_ready=504`) in a fresh dump run, not a stub.
- [x] [BACKEND] P0. Make credentials a first-class readiness dimension (W1 addition 2026-08-19). **Done** (earlier
      this session): `checks.credentials()` wired as the `credentials` leg in `derive_readiness.py:414`, derived
      from UAC's own declared `auth_scope`/`auth_environments`/`supports_testnet`/`supports_mainnet`. Re-confirmed
      live 2026-08-20: present with real counts (`ready=8 not_ready=10 unverified=846`) in a fresh dump run.
- [x] [BACKEND] P0. Make manual execution mode first-class alongside automated (W1 addition 2026-08-19). **Checked
      2026-08-20: genuinely not yet implemented** — no `manual`/`MANUAL` mode reference anywhere in
      `derive_readiness.py` or `checks.py`. Real remaining work, not a stale todo. **Built and shipped same day**,
      `unified-trading-pm@a13d577aea`: `MODES` now `(BATCH, PAPER, LIVE, MANUAL)` per
      `unified_api_contracts.internal.modes.OperationalMode`'s own SSOT (`codex/04-architecture/
      operational-modes.md`) — MANUAL shares LIVE's mainnet endpoint config, so every existing check's
      `mode == "PAPER" -> testnet, else mainnet` mapping already resolves it correctly with no per-check special
      case. Live-tested (`--venue OKX-FUTURES --mode MANUAL`): `execution_orders` correctly resolves via mainnet
      exactly like LIVE; every other leg honestly reports `unverified` since no probe distinguishes
      manual-vs-automated triggering yet. **Caught and fixed a real correctness bug this surfaced**:
      `execution_instruction()`'s `.get(mode.lower(), "none")` treated "no probe field for this mode" the same as
      "probe measured none" — MANUAL initially reported a false `not_ready` instead of honest `unverified`, since
      `InstructionPathAvailability` only models batch/paper/live. Fixed with an explicit absent-vs-measured
      sentinel in the same commit. Confirmed LIVE/PAPER/BATCH unaffected by either change (re-ran, identical
      `ready` verdicts as before).
- [x] [BACKEND] P0. Reconcile the 864-row all-group total quoted in the artefacts (`ready 0 / not_ready 844 /
      unverified 20`) against §17's own table — the artefacts flag it as not reconciled. — **RECONCILED
      2026-08-20**, live full-fleet run against `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json`
      (date=2026-08-19), grain=`instrument_type`, 288 venues × 3 modes = 864 rows. Dump reproduces the artefact
      total **exactly: ready 0 / not_ready 844 / unverified 20**. The figure stands, with denominator (864) and
      date (2026-08-19). Two caveats recorded as their own todos below: the execution-service probe failed in this
      run, and the plan's stated cause for the number is wrong.

- [x] [BACKEND] P0. **The stated critical path is WRONG and should be re-pointed** (measured 2026-08-20). This plan
      and the coordinator both say T4's execution-instruction check is "the structural reason all 864 rows read
      `unverified`". Measured per-leg counts say otherwise: the rows read **`not_ready` (844), not `unverified`**,
      and the dominant failing leg is **`strategy` = 840 `not_ready`** — specifically
      `position_read_mode_availability(venue).<mode> = none`. `execution_instruction` is `unverified` on all 864,
      but rollup lets any `not_ready` dominate, so closing the instruction leg alone moves **zero** rows off
      `not_ready`. The headline number is gated by **strategy position-adapter coverage (strategy-service, T3)**,
      not by T4. Raise with the coordinator before more effort is spent on the assumed critical path. **Raised and
      landed**: `unified-trading-pm@1aa865da41` corrects the coordinator plan's own critical-path claim with the
      full per-leg table cited above — "Re-point the effort at strategy position-adapter coverage" is now the
      coordinator's own stated position, not just this tranche's finding.

- [x] [BACKEND] P1. Fix the execution-service capability probe failing on the full-fleet run. In the 288-venue run
      `_execution_order_capability_probe.py` exited 1 with `No bucket configured for market_data/defi and no
      project ID available`, so `execution_orders` / `execution_fills` / `execution_trades` /
      `execution_account_balance` all reported `unverified=864`. The same probe SUCCEEDS on a single-venue run
      (`--venue OKX-FUTURES` derives `execution_orders=ready` at PAPER and LIVE via
      `validate_operation(place_order, env=testnet|mainnet)`), so this is environmental, not a missing capability.
      The dump degrades honestly, but the published execution-leg counts are a FLOOR, not a measurement — do not
      quote them as capability until this is fixed. **Already fixed, earlier this session** — the "no bucket
      configured" line was a misleading benign log, not the crash cause; the real cause was
      `_place_order_supported()` catching only `UnsupportedOperationError`, not the sibling
      `UnsupportedEnvironmentError` a no-testnet venue (e.g. upbit) raises, crashing the whole subprocess on the
      first such venue and degrading every venue after it. Fixed by catching both (see the function's own
      docstring in `_execution_order_capability_probe.py`). Re-confirmed live 2026-08-20 (full 288-venue run, no
      `--skip-execution-probe`): zero "no bucket configured" errors, real per-venue variance
      (`execution_orders ready=29 not_ready=829 unverified=30`, `execution_fills ready=0 not_ready=816
      unverified=72`) — a genuine FLOOR measurement now, not a crash artifact.
- [ ] [BACKEND] P1. Resolve the per-venue and per-data-type cells that remain pending at the finer grain inside each
      readiness tree. **Same shape as the "close remaining data types" item above — data capture/backfill, not a
      tool or artefact fix. BLOCKED-STANDING-RULE** for the same reason: this tranche does not run backfills.
- [ ] [BACKEND] P1. Fix the tree gaps the artefacts name explicitly — Scroll and zkSync read `unverified — declared,
      never attempted`, and Plasma is `not a ChainKind member`. Consume T1's single chain SSOT; do not re-derive.
      **Investigated 2026-08-20**: T1's SSOT (`unified-api-contracts/unified_api_contracts/registry/chain_env.py`)
      already has all three fully declared — genesis dates, mainnet+testnet chain IDs, and per-protocol onboarding
      dates for SCROLL/ZKSYNC/PLASMA. Neither `readiness-state-dump` nor `honest-coverage-dump` reference chains
      at all (both operate at venue/asset_group/instrument_type grain) — this gap is not a tool wiring defect on
      T5's side. It lives in the artefact HTML's own (evidently stale) chain-status table — held under the
      plan-conflict flag above (`/plans/active/state_fabric_artefacts_2026_08_20.md`), not a separate fix needed.

### Honest coverage — every shard, with a denominator

- [x] [BACKEND] P0. Dump honest coverage per shard across the full shard universe, every figure carrying its
      denominator and date. Engine: `cursor-configs/skills/honest-coverage-dump/` reading the already-computed
      `coverage.json` — never re-derive the expected universe and never re-walk GCS. **Verified live 2026-08-20**:
      `dump_coverage.py` run against `coverage.json` date=2026-08-20 reports per-shard totals with the source
      path and date printed in the header, plus the `dedup_stats` block (distinct-shard count + denominator) added
      today. Tool does this correctly; re-run whenever a fresh figure is needed.
- [x] [BACKEND] P0. Re-run the dump at the finer grain the moment T2 lands `instrument_type` / `data_type` in
      `coverage.json`. The skill auto-detects grain from the payload — verify that, do not assume it.
      **2026-08-20 — the "verify that, do not assume it" half is DONE, `unified-trading-pm@c3a3e870f4`.**
      `tests/test_shard_universe_grain_detection.py`, 7 tests green. The case that matters for this exact handoff:
      when T2 lands the `by_venue_instrument_type_data_type` KEY before landing data under it, a presence-keyed
      detector would flip to the fine grain and enumerate **zero** shard cells — every coverage figure silently
      collapsing while looking structurally fine. The shipped detector requires a non-empty venue block and falls
      back correctly, still reporting the real 2-tuple cells. Confirmed by test, not by reading. **The re-run
      itself is DONE too, 2026-08-20**: T2's axes are landed, run repeatedly today at `instrument_type` grain
      (3965 raw cells, `instrument_type` grain confirmed by `Grain:` header line each time) — no longer waiting.
- [x] [BACKEND] P0. Report the 4-state capture ledger per shard (captured / expected-absent / attempted_failed /
      expected_unattempted) plus a not-expected section for tuples outside the Layer-1 expected universe.
      **Already the tool's core output** (pre-existing, not built today) — confirmed live 2026-08-20:
      `dump_coverage.py`'s human output prints all four states plus a
      `not-expected (stray) = N, Layer-1 holes (missing_tuples) = N` line per asset_group. Nothing to build.
- [ ] [BACKEND] P1. Close the remaining data types the artefacts mark pending — on-chain, sports odds, prediction
      and TradFi vendor datasets. **BLOCKED-STANDING-RULE**: this is data capture/backfill, explicitly banned for
      this tranche ("Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes" — operator ruling
      2026-08-19). "Backfills still running" is itself one of the five allowed pending states for the artefacts —
      not something T5 closes, something T5 reports honestly as in-progress.
- [ ] [BACKEND] P1. Resolve the manifest-hygiene red findings. Evidence:
      `/plans/active/issues/manifest_hygiene_red_all_2026_08_17.md`, `/plans/active/issues/manifest_hygiene_red_all_2026_08_18.md`.
      **Re-checked 2026-08-20**: the 2026-08-18 doc is `status: resolved` (duplicate, closed). The 2026-08-17 doc
      has 10/14 items `[x]` — real diagnosis + 3 confirmed fixes landed (`market-tick-data-service@f67a7480b3`,
      `instruments-service@a586f34102`, plus others cited inline). The 4 remaining `[ ]` are `[DATA]` P2: 2 are
      investigative (git-history check, find-recurring-process), 2 need a VM launch to run
      `detect_manifest_divergence.py` against 14M+-row cefi/tradfi manifests (OOMs locally by design). Not
      attempted here — a VM launch for a non-trivial data audit is a deliberate action, not something to fold
      into a fast batch-flip pass; leaving genuinely open rather than forcing it.
- [x] [BACKEND] P1. Resolve the empty-reprobe disagreement finding. Evidence:
      `/plans/active/issues/empty_reprobe_disagreement_all_2026_08_17.md`. — **Found already resolved 2026-08-20**:
      the issue doc's own `status: resolved` (corrected 2026-08-19), sole todo `[x]` with hard evidence
      (`market-tick-data-service@bf9fe5c4cc`). Nothing to do. (Checkbox-flip oversight from earlier this session
      corrected now — the resolution note was written but the box itself was never ticked.)
- [x] [BACKEND] P0. **No orphans** (epic DoD item, `system_readiness_master.md`) — run the new
      `/shard-utilisation-sweep` skill (consumption verdict per venue/data_type/instrument_type/chain, opposite
      direction from the existing GCS→manifest orphan sweeps; never emits a delete suggestion). **RUN 2026-08-20**
      against `coverage.json` date=2026-08-20, 3,965 shard cells: **venue 158 consumed / 22 not_consumed / 1
      unverified · data_type 18/7/43 · instrument_type 21/3/103 · chain 17/0/10**. Genuinely actionable
      `not_consumed` findings (high confidence, registry vocabulary confirmed adequate): **22 venues absent from
      `VENUE_TO_ASSET_GROUP`** (FOOTBALL 43 cells, FOOTYSTATS 27, AAVEV3 25, BARCHART 10, ODDS_API 7, plus ~15
      individual sportsbooks at 1-2 cells each — `AAVEV3` in particular looks like a `AAVE_V3` casing/typo
      drift, worth checking first); **7 `not_consumed` data_types** (`tradfi/macro_result`,
      `tradfi/yield_curve`, `tradfi/ohlcv_1d`, `tradfi/futures_chain` — T2's repo; `prediction/
      prediction_canonical_question_group`, `prediction/market_lifecycle` + its uppercase duplicate — T2's repo);
      **3 `not_consumed` instrument_types** (`tradfi/nan`, `tradfi/UNKNOWN`, `prediction/nan` — all look like a
      writer emitting a missing-value sentinel into a real column, not genuine orphans; needs the writer checked
      before assuming dead data). The large `unverified` counts are NOT orphans — DeFi's registry declares no
      `data_type`/`instrument_type` vocabulary at all (2,742 DeFi data_type cells and thousands of instrument_type
      cells are simply unmodeled, itself a real finding about the registry's own coverage) and sports' registry
      covers only 1-30% of its own manifest vocabulary (disjoint naming systems, not absence). Since 5 of 7
      not_consumed data_types and all 3 not_consumed instrument_types are in **T2's repos**
      (instruments-service/market-tick-data-service), routing via the standard T5→T2 inbound-request protocol
      rather than acting directly — filed below.

### W4 — observability, alerting and auto-recovery

- [x] [BACKEND] P0. Close the `dp_cron_did_not_fire` alert defects — the storm recurring on a stable revision, dedup
      state lost on redeploy, and the volatile dedup field. Evidence: the three
      `/plans/active/issues/dp_cron_did_not_fire_*` docs. **2026-08-20 status: all three fixes ARE shipped and
      tested (`alerting-service` `core/recurring_dedup_persistence.py`, `f48a611` + `ac21303`, 14 tests green).**
      **Verification CLOSED, 2026-08-20** — the earlier "UNVERIFIED, gcloud expired" blocker no longer holds:
      gcloud auth is live this session. Confirmed serving revision `dp-alerting-subscriber-00141-8nb` (100%
      traffic, asia-northeast1, deployed 18:15Z) carries the fix — its file content is byte-identical to the fix
      commit (SHA ancestry doesn't survive the LDR→main squash-style promote, so content-diff was the right test,
      not `--is-ancestor`). Three independent post-deploy measurements now agree the storm is resolved: a 06:55Z
      dedicated sweep (found + fixed a second contributing cause, a duplicate Cloud Run Job consumer), a 12:37Z
      24h re-sample (per-identity cadence ~25-26min against the 1800s cooldown, compliant), and this session's own
      92-min/64-msg re-check (max 3 repeats per identity, consistent with the cooldown holding). Remaining volume
      traces to genuine DP-LIVE-004/003 capture gaps (real, ageing, out of T5 scope), not the dedup bug. Evidence:
      `/plans/active/issues/dp_cron_did_not_fire_still_storming_after_gcs_persistence_fix_2026_08_20.md`.
- [x] [BACKEND] P0. Fix the escalation-pool-exhaustion alert being unreachable when halted. Evidence:
      `/plans/active/issues/escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18.md`. — **Found
      already shipped, 2026-08-20** — `agent-orchestrator@78a9a02c` (2026-08-19), 9 regression tests confirmed
      passing on current code. The issue doc's own `status: open` was stale for an already-fixed, already-tested
      defect; corrected in place rather than re-implemented. Its P3 live-verify todo stays genuinely open — needs
      a real future exhaustion window's journalctl output this pass does not have.
- [x] [BACKEND] P1. Verify every actionable alert that pages an OPEN gets a ✅ CLOSE bookend in-channel. SSOT:
      `/codex/04-architecture/agent-orchestrator-alerting.md`. **Verified 2026-08-20** via two independent layers:
      (1) code — `agent-orchestrator/tests/test_alert_quality_overhaul.py`, 29/29 passing, including the two
      SSOT-cited test-locks (`test_escalation_resolved_pages_only_when_it_previously_paged`,
      `test_account_auth_recovered_still_pages`); the git-staleness close path
      (`_maybe_fire_staleness_resolved`, `server/worker_liveness/_git_alerts.py:631`) is structurally guarded —
      `if kicker._last_staleness_alert.pop(key, None) is None: return` — so the close notifier can never fire for
      a condition that never paged OPEN. (2) live traffic — read `#agent-orchestrator-alerts` for the trailing 24h
      (504 msgs). Every BLOCKED-question-answered message carries "closes the BLOCKED question opened `<ts>`
      (`BLK-xxx`)"; every git-RED-recovered message either carries "closes the RED alert opened `<ts>`" or falls
      back to a bare "RECOVERED" line — traced the bare form to `notify_git_staleness_resolved`'s own documented
      fallback (`opened_at` lives in an in-memory, non-persisted dict; a server restart mid-episode loses it while
      the persisted "was alerted" flag survives — an acknowledged degradation, not a silent-close bug: the
      bookend still fires, only the timestamp-correlation detail is sometimes missing). Found no instance of an
      alert paging OPEN with no matching close in the observable window. Not exhaustive over multi-day history
      (several `[OPERATOR]` questions open before the 24h window couldn't be traced to a close from this sample
      alone) — scoped to what the window could actually show, not claimed beyond it.
- [x] [BACKEND] P1. Complete the E2E wiring reachability audit. Evidence:
      `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md` (11 open). **Mis-scoped at authoring,
      corrected 2026-08-20**: the doc's own frontmatter `repos:` is `[strategy-service, execution-service,
      unified-api-contracts, system-integration-tests]` — only `system-integration-tests` is T5-owned, and none
      of the 11 open items name it (verified: grepped the full open-item text for `system-integration-tests`/`sit`,
      zero hits). 1 is `[OPERATOR]` P0 (a blocking design ruling), 1 `[AGENT]` P1 explicitly says "resolve as a
      LOCAL/operator-scoped design todo... before dispatching" and touches `execution-service`/`strategy-service`,
      1 `[AGENT]` P2 is a disclosure-artifact fix outside T5's four artefacts, and 7 are a distinct
      OTC-reconciliation/MiFID-audit-trail finding cluster (booking, reconciliation engine, audit coverage) —
      none of which is E2E-wiring-reachability subject matter and none of which sits in a T5 repo. Not fixing
      cross-repo per the tranche's own "edit ONLY the repos you own" rule; these belong to whichever tranche(s)
      own `strategy-service`/`execution-service` (T3/T4 per the coordinator's allocation) and are already visible
      to them via this same issue doc — no new inbound request needed since it's not a T5-discovered gap.
- [x] ✅ [BACKEND] P2. Fix the SIT stamp-dispatch 503 false positive. Evidence:
      `/plans/archive/2026_08/issues/sit_stamp_dispatch_503_false_positive_2026_08_17.md` (archived 2026-08-20,
      resolved). **Implemented the doc's own
      follow-up exactly as specified**: `full-workspace-sit.yml`'s Stamp step now emits
      `failure_class=stamp_infra_only` when `STAMP_FAILURES` fires but every per-repo invariant result was PASS,
      propagated through the "Report SIT result to PM" dispatch (switched `gh api -f` → curl+JSON since `-f`
      cannot express a nested `client_payload` object) to `sit-unlock.yml`'s escalate-to-orchestrator step, which
      now branches its `CONTEXT` message instead of always asserting "identify which pending repo broke it".
      `system-integration-tests@5b592dce92`, `unified-trading-pm@5247fe641a`. Both YAML files verified to parse
      (`python3 -c "import yaml; yaml.safe_load(...)"`) before shipping; not runtime-tested against a live GitHub
      503 (would need to fabricate one), so the CONTEXT-branching logic itself is unverified in production — the
      per-file landed content is confirmed, the end-to-end behavior on a real recurrence is not.

### W21 — the presentation artefacts (the acceptance test)

> **⚠️ PLAN-CONFLICT FOUND, 2026-08-20 (T5)** — before hand-editing ANY of the four DOC todos below, read
> `/plans/active/state_fabric_artefacts_2026_08_20.md` (authored 2026-08-20 15:04, different session, `status:
> active`, unclaimed, `parent_epic: system_readiness_master` — same epic as this plan). It measured
> `platform-external-api-walkthrough.html` as "a rollup, not a drilldown" (8 percentage values, zero shard-level or
> per-day vocabulary) and diagnosed the root cause as exactly this tranche's own standing failure mode: numbers
> hand-transcribed into HTML with no persisted source, so they rot. Its fix is architecturally different from "edit
> the HTML directly against a skill's output" — it wants a **persisted, versioned readiness+coverage ledger** that
> the artefacts RENDER FROM, explicitly naming `readiness-state-dump` and `honest-coverage-dump` (the two tools
> this tranche owns and extended today — grain fix `065067f345`, dedup stats `bb81afbcaa`, execution-instruction
> wiring `8d47cf3393`) as the ledger's authoritative source. Hand-editing the four HTMLs below right now risks being
> reworked/wasted once ledger-binding lands. **Also corrects scope**: seven artefacts need updating against the
> 27 R17-R27 rulings, not four — `platform-api-reference`, `carveout-engineering`, `ODUM_Elysium_Phase2_Update`
> were missing from earlier accounting (the last two are outside this plan's originally-scoped four). Holding these
> four todos pending coordination on which approach to follow — not starting a manual re-derivation that the ledger
> plan would then have to undo.
>
> **OPERATOR DECISION, 2026-08-20**: wait for the ledger plan. Do not hand-edit the artefacts. These todos (and the
> disclosure-standard-extension + figure-measurement-confirmation items below that are the same class of work)
> stay held until `/plans/active/state_fabric_artefacts_2026_08_20.md` lands its ledger-binding, or until that
> plan is explicitly reprioritized. Next session: check that plan's status before resuming any of these — do not
> re-litigate this decision without a changed premise.
- [ ] [DOC] P0. Re-derive `platform-architecture.html` from measured state. Every remaining marker must be live or
      one of the five allowed pending states.
- [ ] [DOC] P0. Re-derive `platform-external-api-walkthrough.html` — the heaviest artefact by gap count (28
      `unverified`, 27 `pending`, 17 `planned`, 17 `partial`, 14 `not yet`, 6 `missing`, 5 `not built`).
- [ ] [DOC] P0. Re-derive `strategy-service-deep-dive.html` (51 `unverified`, 15 `partial`) against T3's output.
- [ ] [DOC] P0. Re-derive `strategy-service-walkthrough.html` (23 `partial`) against T3's output.
- [x] ✅ [DOC] P2. **[OPERATOR]** Complete `platform-api-reference.html`'s type-support table — add the two rows it
      still omits, `WITHDRAW`/`WithdrawInstruction` and `REPAY`/`RepayInstruction`. UAC `StrategyInstructionEnvelope`
      grew 11→13 subclasses (`f5fc118a` 2026-08-20); the count/prose enum-drift fix shipped separately (that was the
      promote-PR QG red), so the table still lists 11 of 13 rows. Adding the 2 rows adds 2 `st-plan` markers →
      claim-ownership open-markers 189→191, tripping the shrinking ratchet. Operator-gated: bump the markers baseline
      (never hand-raise), or close 2 other open markers by real state change first.

      **PARTIALLY RESOLVED 2026-08-21 — `unified-trading-pm@f28330fafc`.** Netted rather than bumped the baseline:
      closed one genuinely-resolved marker in `carveout-engineering.html` §09 ("Appendix — the source estate") —
      its `ev-check` → `ev-verified`, citing `strategy-service@efa1525813`'s now-landed `EXTRACTION_AUDIT.md` (the
      per-repository code-coupling measurement that §09's own 26-repo contribute/non-contribute table asserts — see
      `elysium_carveout_stubbed_strategy_service_2026_08_12.md`'s 2026-08-16 Progress Log entry). Checked the other
      3 candidate-resolved todos in that same plan (PortfolioRiskService live-values ruling ~L124, frozen
      collateral-eligibility ruling ~L169, health_factor/usdc_idle_yield data-scope resolution ~L236) against the
      artefact's actual prose — none maps cleanly to a whole-section claim: the PortfolioRiskService/risk-guards-local
      write-up todos in that plan's own §B are still `[ ]` unchecked, i.e. `carveout-engineering.html`'s prose was
      never updated to match the 2026-08-16 ruling, so upgrading its marker now would be the exact "marker with no
      genuine state-change behind it" failure mode the ownership rule exists to prevent; the collateral-eligibility
      ruling covers only one row of §05's multi-claim table (not that section's whole claim) and its own text says
      "still open, not yet done" for the actual substitution build; the data-scope resolution has no corresponding
      section in this artefact at all. Only 1 of 4 closed safely, so added only 1 new row
      (`WITHDRAW`/`WithdrawInstruction`), not 2, to stay net-zero — `REPAY`/`RepayInstruction` remains a documented
      gap in the table, needing either a second genuine marker close elsewhere or an operator-approved baseline
      bump. Net check: `check_artefact_claim_ownership.py` open-markers held at **189** (no baseline bump used) —
      `carveout-engineering.html` 17→16, `platform-api-reference.html` 28→29. Verified per-file against
      `origin/live-defi-rollout` (not just local HEAD), commit `f28330fafc`.
- [x] [DOC] P0. Verify the invariant the epic sets — **every claim-bearing artefact section maps to a tracked
      item**. Build the check; it has already failed once, measurably. — `unified-trading-pm@7b2dd29aaa`.
      `scripts/plan-hygiene/check_artefact_claim_ownership.py`, wired into `run_hygiene_sweep.sh`. Measured
      2026-08-20 over the 7 artefacts: 84 top-level sections, 83 claim-bearing, **37 carrying no `owner:` tag**,
      189 open markers (st-part + st-plan + ev-check + ev-assumed), 55 closed. The invariant is confirmed FAILING
      and is now ratcheted — both counts can only go down. Owner resolution reads the tag's `title` attribute (the
      machine-readable doc path) before the visible label; label-only resolution produced 3 false violations on
      this corpus, so the checker was corrected before seeding rather than baselining the lie.

      **INVARIANT NOW SATISFIED, 2026-08-20 — 37 → 0.** Every claim-bearing section in every artefact carries a
      real `owner:` tag, each citing a doc verified to exist on disk (not invented): `platform-architecture.html`
      (13 sections) → `system_readiness_master` (readiness matrix, data coverage, batch=live spine, funds-isolation
      hard rule, risk/isolation, expansion breadth, definition-of-done) / `execution_master` (algorithm selection)
      / `elysium_october_delivery_and_code_disclosure_readiness` (Phase 2 archetype scope) /
      `code_readiness_t5_readiness_observability_presentations` (the CI/delivery section — literally T5's own
      repos, agent-orchestrator + unified-trading-ci); `carveout-engineering.html` (9 sections) → the Elysium
      carve-out spec plan; `strategy-service-deep-dive.html` (10 sections) → `strategy_master`;
      `strategy-service-walkthrough.html` (1) → `strategy_master`; `platform-external-api-walkthrough.html` (1) →
      `system_readiness_master` W21; `platform-api-reference.html` (2) → `system_readiness_master` W21 and, for
      the Authentication section specifically (T1's `unified_trading_library/cloud_interface/api_auth.py`), →
      `code_readiness_t1_contracts_library_externalapi` — the correct owning tranche, not force-fit into T5's own
      epic. Baseline lowered `37→0` / markers held at `189` (no regression). Verified via
      `check_artefact_claim_ownership.py` after every batch, not just at the end — one self-correction caught
      mid-pass (an early edit added a spurious duplicate marker instead of only an owner tag; found by re-running
      the checker before shipping, fixed before it ever landed).
> **Same plan-conflict applies below** — the disclosure-standard extension is the same class of
> hand-HTML-edit work `/plans/active/state_fabric_artefacts_2026_08_20.md` would supersede; it also names
> `carveout-engineering.html`/`ODUM_Elysium_Phase2_Update` as in-scope for its corrected 7-artefact count.
- [ ] [DOC] P0. Extend the same disclosure standard to the four sibling client artefacts the 2026-08-18 audit found
      violating it and which no remediation plan covers — `carveout-engineering.html` and
      `ODUM_Elysium_Phase2_Update_2026-07-24.html` alongside the two already in scope. Evidence:
      `/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md`,
      `/plans/active/client_artefact_remediation_nickai_2026_08_18.md`.
- [ ] [DOC] P0. Confirm no figure outruns its measurement — every number carries date and denominator, or says
      pending. Epic definition-of-done item.

### W19, W20 — corpus and automation

- [x] [AGENT] P1. Run the corpus audit — nothing relevant left un-folded, nothing stale left believed. Epic
      definition-of-done item. Use `/plan-reconcile` and `/docs-reconcile`. — **Confirmed run today, 2026-08-20**:
      full-corpus `/plan-reconcile` sweep landed at `unified-trading-pm@2af2763f9b`
      (`/plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md` — 892 docs read in full, 301
      findings, all 3 P0 + all 33 P1 actioned; P2/P3 long tail converted to tracked class-level todos, not left
      as ephemeral findings). `/docs-reconcile` already confirmed run today per the entry below. Both audit tools
      ran this session-day; the remaining findings from either are tracked work, not an un-run audit.
- [ ] [AGENT] P1. Fix the docs-reconcile findings and the remaining broken links. Evidence:
      `/plans/active/issues/docs_reconcile_findings_2026_08_17.md`,
      `/plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md`. **Checked 2026-08-20, corrected**:
      first pass at this mischaracterized the remainder as "mechanical" without reading each item — on actual
      read, most of the ~13 P2/P3 items are already well-triaged and genuinely stuck on human judgment (ambiguous
      redirect targets, doc authorship, content-reconciliation calls), each already carrying its own "needs a
      human" note from prior audit passes; force-fixing them would mean guessing, which the prior passes correctly
      declined to do. One item WAS resolvable: the root `README.md` P2 finding had gone stale in the other
      direction — the 3 claims it named were already fixed by another session since 2026-08-02 — flipped with
      evidence, `unified-trading-pm@2d743a57d3`. Genuinely 2 `[OPERATOR]` decisions + ~11 human-judgment items
      remain; not a bounded mechanical pass.
- [x] [AGENT] P2. Land the AO watchdog scheduled-timer wiring. Evidence:
      `/plans/active/issues/ao_watchdog_scheduled_timer_wiring_2026_08_17.md`. — **Checked 2026-08-20**: the
      wiring itself is done — 6 of 7 todos `[x]` (dispatch handler, role wrapper, install script, cadence update,
      tests, operator cadence decision). The sole remaining item is `[OPERATOR] P2. Re-run
      install-ao-watchdog-timer.sh on the central orchestrator VM` — needs VM SSH access this tranche doesn't
      have, genuinely operator-owned, not a T5 code gap.
- [x] [BACKEND] P1. **NEW 2026-08-20** — `agent-orchestrator`'s quality gate fails on a stale `dashboard/node_modules`
      (missing `@vitest/coverage-v8`), unrelated to any specific change — blocks EVERY future ship to this repo, not
      just one. Fix: `npm --prefix dashboard install` (or equivalent dependency sync) before the next
      agent-orchestrator ship attempt. Found blocking the git-status ahead-nudge sustain-gate fix below; that fix and
      its 2 regression tests are complete and tested locally (26/26 file, 103/103 broader suite) but NOT YET SHIPPED
      — preserved both in the working tree and backed up outside git
      (`scratchpad/agent-orchestrator-backup/_git_alerts.py` + `test_git_staleness_alerting.py`) since this session
      already measured local uncommitted edits as fragile under quickmerge contention. **Resolved 2026-08-20**:
      this was per-checkout local environment state, not a repo code defect — `npm --prefix dashboard install` ran
      once, and every subsequent agent-orchestrator ship this session gated clean on it. Moot now regardless: the
      git-status-nudge fix this was blocking landed at `agent-orchestrator@0ec1f010d2` (see below).

### Infrastructure defects that cost other agents time

- [x] [BACKEND] P1. Fix `git stash push/pop` silently dropping content under high branch velocity — this defect
      costs every tranche real work. Evidence:
      `/plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`.
      **DONE 2026-08-21**: both extracted items in `/plans/active/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md`
      landed — item 1 (repro of both the stale-pathspec and transient-empty-pathspec hypotheses, both confirmed)
      at `unified-trading-pm@9e5e873988`, item 2 (promoted the confirmed `git pull --rebase --autostash` per-batch
      fix into `/codex/05-infrastructure/per-tab-worktrees.md`) at `unified-trading-pm@e022d3f0e3`. This doc's own
      remaining items are P3 conditional-future ("if velocity recurs") or a P2 design-review call, neither
      blocking this tranche.
- [x] [BACKEND] P1. Add the retry safety net for `main-backmerge-to-ldr` on non-PM repos. Evidence:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md`.
      **Re-verified 2026-08-20: all three extracted fixes are landed and cited in the source issue —
      `unified-trading-pm@96c163347f` (fleet-wide drift-tick), 25 caller-stub commits (comment correction), and
      `unified-trading-pm@2ead733819` (failed-backmerge detection). This doc's own remaining item is a P3
      third-party-action-pinning evaluation.**
- [x] ✅ [BACKEND] P1. Fix the `unified_trading_ci` FF-pull cron branch-override gap. Evidence:
      `/plans/active/issues/unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md`. **The core defect
      is fixed**: `unified-trading-ci main` added to `scripts/dev/cron-branch-overrides.txt` (`[x]`), verified no
      new spurious `wip-preserve/` branches post-fix (`[x]`), and a CI/QG check now asserts every
      `workspace-manifest.json` repo with a non-default integration branch has a matching override entry (`[x]`).
      Remaining open items in that doc are 2 `[OPERATOR]` P3 decisions (registry collapse, reconciling specific
      stale local slots) and 1 `[BACKEND]` P2 monitoring enhancement (fleet-wide quarantine rollup) — none of
      these are the gap this todo names, so not blocking this close-out.
- [x] ✅ [BACKEND] P3. Fix the git-status red-nudge false positive from the wrong branch comparison. Evidence:
      `/plans/active/issues/git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md`. **Both
      original todos were already `[x]`, shipped 6 days prior. Its 2026-08-19 addendum named a third, still-open
      mechanism (`maybe_nudge_on_red_repos`'s `ahead` branch has no sustain gate) — FIXED + TESTED, NOT YET
      LANDED, do not tick without a sha.** `server/worker_liveness/_git_alerts.py`, gated on `not_clean_since`
      sustained past 600s matching the function's own `behind`-branch precedent. 2 new regression tests, 26/26
      file passing, 103/103 broader suite passing.

      **BLOCKED-INFRA, 2026-08-20 — 3 ship attempts, correctly stopped rather than blind-retried a 4th time.**
      Attempt 1 failed on stale `dashboard/node_modules` (fixed via `npm --prefix dashboard install`, confirmed
      `@vitest/coverage-v8` present afterward). Attempts 2 and 3 both failed with the IDENTICAL generic banner
      `❌ Re-gate FAILED against the current tree` and **no specific check name anywhere in either log** — attempt
      3's log was captured in full (9,265 lines, no `tail` truncation this time) specifically to rule out my own
      earlier self-inflicted truncation as the cause; the vitest suite immediately above the failure shows 20/20
      files, 468/468 tests passing, then the banner fires with nothing in between. A **standalone**
      `bash scripts/quality-gates.sh --no-fix` run against this exact tree produced **zero** `❌` lines. Two
      identical consecutive failures with a clean standalone gate is the documented signal to stop retrying and
      diagnose deeper, not flap — this looks like quickmerge's own re-gate wrapper losing or swallowing a
      per-check result under the heavy fleet contention observed all session (5-13 concurrent quickmerge
      processes), not a defect in this fix. The fix remains preserved in the working tree AND backed up outside
      git (`scratchpad/agent-orchestrator-backup/`). Needs either a lower-contention retry window or someone with
      quickmerge-internals context to diagnose why re-gate's failure path drops its own check name.

      **ROOT CAUSE FOUND + FIXED, 2026-08-20 (4th attempt, fleet contention independently confirmed low — only 1
      other quickmerge running, a different repo).** Attempt 4 reproduced the identical symptom, ruling out
      contention as the sole explanation. Read `scripts/quickmerge.sh`'s re-gate diagnostic path directly
      (~L2560-2571): the branch that decides "real failure vs. lost race" classifies on
      `grep -E '❌|^FAILED |^ERROR |^E '`, but the very next line that PRINTS the evidence to the agent only
      grepped literal `grep '❌'` — a failure surfacing as a bare pytest `FAILED test_x` / `E AssertionError`
      line (no ❌ emoji) is correctly classified as real but the display step matches nothing, producing exactly
      the observed banner-with-no-check-name. **Fixed**: broadened the display grep to the same 4-pattern set used
      for classification, plus a fallback message (naming the regate exit code + the manual command to run) for
      the case where even that finds nothing. Pure diagnostic-string change — no pass/fail semantics touched.
      `scripts/quickmerge.sh` is the PM SSOT every repo's own copy symlinks to, so this fixes the diagnostic gap
      fleet-wide, not just for this ship. `unified-trading-pm@897067dc0b`. Re-attempting the
      agent-orchestrator ship now that the fix is in place; if it still fails, the new diagnostic should finally
      name the real check.

      **LANDED, 2026-08-20 (6th attempt) — `agent-orchestrator@0ec1f010d2`, verified per-file against origin (both
      `not_clean_since` in `_git_alerts.py` and both new test names in `test_git_staleness_alerting.py` present).**
      The 5th attempt reproduced the identical banner even with the quickmerge.sh fix in place — the broadened
      grep DID work exactly as designed (confirmed by reading the raw log: it correctly found and printed the
      generic rollup line `❌ agent-orchestrator quality gate FAILED`), which finally revealed the real defect was
      **one layer further in**: that literal string is `agent-orchestrator/scripts/quality-gates.sh`'s own
      unconditional final message (line 254) when its internal `FAIL` flag is set — and the `run()` helper that
      sets that flag (line 102: `"$@" || FAIL=1`) prints **no diagnostic of its own**, only a `── section ──`
      header before the command runs. So the true failing check was invisible to BOTH quickmerge's summary line
      AND my own earlier manual `grep '❌'` verification of a standalone gate run — because the actual failure text
      was `Would reformat: server/worker_liveness/_git_alerts.py` (from `ruff format --check`, under the
      `── ruff format --check — server/ ──` header), which matches neither `❌` nor `FAILED `/`ERROR `/`E `. My
      own fix's long inline comment block was ruff-format non-compliant (a line-wrap preference, not a lint error
      — `ruff check` passed clean the whole time, only `ruff format --check` objected) — every prior "clean
      standalone gate, zero ❌ lines" check I ran was true and simultaneously missed this, since I was grepping
      the same narrow pattern. Fixed with `ruff format server/worker_liveness/_git_alerts.py` (pure re-wrap of one
      long f-string call, no semantic change — 26/26 regression tests re-confirmed passing after), then shipped
      clean on the first attempt. **Lesson for future sessions**: `ruff format --check` failures print
      `Would reformat: <path>`, not `❌`/`FAILED`/`ERROR` — no diagnostic-string grep pattern will ever catch
      every failure shape a gate can produce; when a "REAL failure" banner fires with no visible evidence, the
      reliable move is `git diff` the exact files being shipped through each individual formatter/linter directly
      (`ruff format --check <path>`) rather than trusting a keyword grep over the full log a second time.

### Close-out

- [x] ✅ [AGENT] P1. Work the non-spine tail of this tranche's 433-doc allocation to zero open todos or an explicit
      `BLOCKED-*` tag. This is the largest tail of the five — expect AO, CI and plan-hygiene work. **DONE 2026-08-20**
      — all 352 tail docs carrying an open todo (135 P0/P1 + 217 P2/P3; the other 62 of 414 non-spine docs already
      sat at 0 open todos) triaged in full via 15 parallel read-only sub-agents (~22-25 docs each, 3 waves of ≤5),
      each doc read completely (not just its todos section) and cross-checked against live code/`git log`/sibling
      docs, not re-read on trust. Applied 24 docs' worth of real, evidence-backed fixes (~37 checkbox flips + inline
      `BLOCKED-ON:`/`BLOCKED-OPERATOR-DECISION` tags) across two ships
      (`unified-trading-pm@395e27e8d4`, `@cd639cec06`), plus archived 2 fully-resolved docs
      (`manifest_hygiene_daily_malformed_frontmatter_blocks_quickmerge_2026_08_19.md`,
      `prosewrap_padding_baseline_climbing_recheck_2026_08_16.md`). Low yield by design, not failure — this corpus
      already runs `na-eligibility-audit`/`plan_reconciler`/`context-scout` on a recurring cadence, so most open
      todos were already correctly classified; the value here was the ~24 genuine misses those passes don't check
      for (a todo's own stated done-when condition silently met elsewhere, an evidence-embedded-but-unflipped
      checkbox, a blocked item never machine-tagged as such). One doc's 2 fixes couldn't ship
      (`cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` — already over the 1000-line hard cap before this
      pass touched it, a pre-existing structural blocker `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`
      already documented; reverted rather than force through the gate). Remaining open todos across the tail are
      genuinely open — operator-gated decisions, machine-`gate_on_depends`-blocked finalize plans awaiting a parent
      that isn't done, or real unstarted engineering/ops work — not a bookkeeping gap.
- [x] [AGENT] P3. ✅ **DONE 2026-08-21**: line-cap block cleared (another session split the doc's history out to
      `cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`, 1093→650 lines) — applied both fixes,
      `unified-trading-pm@8f76f9e85f`. Apply the 2 verified-but-unshipped fixes in
      `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` once its pre-existing line-cap block clears (see
      that doc's own item 1 / `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md` line 290 for the
      blocker — needs either a real split or a 5th operator-ruled `check_line_caps.sh` carve-out). Both verified
      2026-08-20, evidence still valid:
      1. The "Bisect test_dp_recovery_actuators.py's full-suite contamination" todo (`[CODE] P2`) — flip `[x]`,
         already resolved: source doc `plans/archive/2026_08/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`
         is `status: resolved`, fixed by `deployment-service@0c38c00d` (an autouse conftest fixture isolating
         LocalStorageProvider's shared tempdir), full QG re-verified green (3332 passed, all 11 actuator tests).
      2. The "Step 3 cross-data_type completeness capture per venue_data_types.yaml" todo (`[CODE] P2`) — flip
         `[x]`, already resolved: the block's own inline note ("NOT ACTIONABLE 2026-08-15, mis-scoped for a single
         AO dispatch, re-scoping filed separately") confirms investigation is complete and the work was correctly
         re-filed to `plans/active/issues/cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md`
         (confirmed exists) — matches this doc's own established "diagnosed → re-routed → flip [x]" pattern used on
         neighboring items.
- [ ] [AGENT] P0. Post-phase codex audit for every contract changed.
- [ ] [AGENT] P0. **Final gate for the whole effort** — confirm all four artefacts carry no `pending`, `planned`,
      `partial`, `not built` or `unverified` marker outside the five allowed states, and that every number carries
      its denominator and date.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

- 2026-08-20 — **Root `README.md` staleness fixed** (the concrete, mechanically-verifiable subset of the
  `docs_reconcile_remaining_broken_links_2026_08_02.md` P2 finding — the doc's own prior audits deliberately
  scoped this out as "needs a real onboarding-doc pass," which is why it survived 6+ na-eligibility passes;
  narrowed here to only claims verified against the live filesystem/git history, not guessed):
  `scripts/workspace/sync-rules-pull.sh` and `sync-workspace.sh` do not exist (confirmed via `find` + `git log
  --diff-filter=D`: removed in `8c18241537` when the workspace moved from a rules-sync model to a
  `.cursor/rules/` symlink — `setup-cursor-rules-symlink.sh`); the "Quickmerge... creates a branch, and opens a
  PR" claim contradicted the actual default flow (direct commit to `live-defi-rollout`, no branch/PR — confirmed
  `grep` on `quickmerge.sh` for rule-sync/PR-create logic, cross-checked against this same CLAUDE.md's own
  `ci-cd-flow.md` pointer); `unified-trading-codex` is listed as a live sibling repo in two places but is
  ARCHIVED (per this file's own CLAUDE.md); the workspace-structure diagram showed the pre-Path-B flat clone
  layout, missing the `.tabs/<N>/` per-slot worktree model live since 2026-06-08 (confirmed against
  `/codex/05-infrastructure/per-tab-worktrees.md`). 7 fixes, `unified-trading-pm@2d743a57d3`. The
  remaining ~16 items in that issue doc and its 2026-08-17 sibling stay open — genuinely VALID_JUDGMENT per
  6+ independent na-eligibility-audit passes, not re-litigated here.

- 2026-08-20 — **The acceptance test now exists and is machine-enforced** — `unified-trading-pm@7b2dd29aaa`.
  `scripts/plan-hygiene/check_artefact_claim_ownership.py` + `artefact_claim_ownership_baseline.yaml`, wired into
  `run_hygiene_sweep.sh` next to the disclosure and enum-drift checks.

  **Measured, 7 artefacts under `codex/14-customer-journeys/commercial-model/`, 2026-08-20**: 84 top-level
  sections · 83 claim-bearing · **37 with no `owner:` tag** · **189 open markers** · 55 closed. Both counts are
  seeded as shrinking ratchets, so the effort's progress is now a number that can only fall. Per-artefact open
  markers: walkthrough 53 · walkthrough(strategy) 36 · architecture 29 · api-reference 28 · deep-dive 26 ·
  carveout 17 · ODUM 0.

  Marker vocabulary is read from the artefacts' own markup (`st-part`/`st-plan`/`ev-check`/`ev-assumed`), not a
  hand-copied list, and legend blocks are stripped first — the legend defines the vocabulary and contains a
  literal `owner: W5` example that would otherwise hand every artefact a free ownership tag.

  **Two corrections made before shipping, both cases of a claim outrunning its measurement:**
  1. First cut resolved owner tags from the visible label only and reported 3 dangling references
     (`elysium-disclosure §C`, `elysium-disclosure §H.8`, `registry ground-truth P0`). Reading the markup showed
     all three carry a real repo-relative doc path in their `title` attribute. That was the checker's blind spot,
     not an artefact defect — fixed, and the checker now also verifies the cited doc exists on disk.
  2. `quickmerge` exited 0 while the gate FAILED on two E501 violations and nothing landed. Caught only by
     checking `origin` directly. Re-shipped after fixing. Exit 0 from a piped ship script is not evidence.

- 2026-08-20 — **`execution_instruction` leg: the SKILL.md pointer was wrong, and the real blocker is now named.**
  Shipped — `unified-trading-pm@c3a3e870f4` (all 5 files verified individually in origin, not by exit code).

  `readiness-state-dump/SKILL.md` pointed this leg at `execution-service/execution_service/v2/policy_resolver.py`,
  calling it "the real `InstructionActionV2`-adaptor registry". **It is not.** Measured 2026-08-20: that module
  resolves an execution *algorithm* keyed by `(client_id, slot_label)`, with venue appearing only as one
  `applies_to` gate dimension (`venue_category`). It never answers "can this venue execute this action". Corrected
  in place — a pointer that cost one agent a wrong-file read will cost every future agent the same.

  The only action-keyed dispatch that exists is `backtest_v2/action_handlers.py::resolve_settlement`, which is
  **venue-independent and backtest-scoped**. Measured via AST: **11/16 `InstructionActionV2` actions have a
  settlement path** (10 handled + `CANCEL` control-plane no-fill by design); **5 raise `UnhandledActionError`:
  `CONVERT_DUST`, `LP_BURN`, `LP_MINT`, `REPAY`, `WITHDRAW`** — `REPAY`/`WITHDRAW` are core lending actions and
  `LP_MINT`/`LP_BURN` are what the enum's own comment says the DEFI_LP_CONCENTRATED engine emits.

  **The leg still prints `unverified` per venue, deliberately.** The measured gap is global and backtest-scoped,
  so folding it into the 864 rows as `not_ready` would assert something this pass did not measure and would make
  every row fail for the same non-venue-specific reason. It is surfaced once, as a dump-level finding.

  **Rejected as drift**: mapping `InstructionActionV2` onto UAC `operation_details` keys. That vocabulary is
  per-venue idiosyncratic — measured `place_order` / `create_order` / `new_order` / `post_order` / `add_order` /
  `submit_order` / `buy`+`sell`, mixed with feed endpoints (`l2_book`, `all_mids`, `ws_trades`) across 47 of 67
  registered sources. Any hand-built map would silently misread venues spelling their order verb differently.

- 2026-08-20 — **W4 alerting: the fixes are shipped; what is missing is verification. Live measurement taken.**

  Went to re-implement the `dp_cron_did_not_fire` dedup fix and found it **already shipped with tests** —
  `alerting-service/alerting_service/core/recurring_dedup_persistence.py` (`f48a611` GCS-persisted cooldown,
  `ac21303` merge-before-write closing a lost-update race), 14 tests green, wired into
  `router._is_duplicate_alert` for `_RECURRING_ALERT_COOLDOWNS`-eligible events only. All three predecessor issue
  docs still read `status: open`. Re-implementing would have been pure waste.

  **Live ground truth** (`scripts/dev/slack-read-channel.py data-pipeline-alerts 24`, read-only): **3,008 alert
  messages** over 2026-08-18T23:20Z → 2026-08-19T23:02Z, **2,509 of them `DP_CRON_DID_NOT_FIRE`**. Prior sweeps on
  08-17 and 08-18 both recorded 150/24h — a **20× increase**, not a residual tail.

  The fix reached `main` at 2026-08-19T21:41:59Z. Split there: PRE-fix 2,826 msgs / 22.5h (126/h), 47 of 61
  repeating identities breaching the 1800s cooldown; POST-fix 182 msgs / 1.0h (182/h), **41 of 46 still
  breaching**, typical identity firing every **13.0 min** — one per detector sweep, as if no cooldown engaged.

  **What this does NOT establish, deliberately**: that the fix is ineffective. `gcloud run services describe
  dp-alerting-subscriber` failed with `Reauthentication failed`, so the serving revision during that hour is
  **unverified**, and landing on `main` is not deployment. A 1h window spans only ~2 cooldown periods. Recorded as
  `BLOCKED-CREDENTIALS` rather than guessed at.

  **A correction made mid-investigation**: I first read `origin/main` locally, concluded the fix was NOT on main,
  and nearly filed a "promotion stalled, 296 commits unpromoted since 2026-08-01" finding. Checking the remote
  directly (`gh api .../contents/...?ref=main`) showed the file IS on main. The local check was wrong twice over: a
  stale cached ref, and `merge-base --is-ancestor` cannot see through the squash-style Option-B promote, so it
  reports NO for a commit whose content did land. Cached `origin/` is a proxy, exactly as CLAUDE.md says.

  Also separated the alert bug from the real conditions underneath: much of the volume is **many distinct
  identities**, which dedup is correct not to collapse (the 22:51Z burst is 13 different sports books on one VM).
  Those are real capture gaps — sports odds **never captured**, CME trades **8.0d stale** (5.0d on 08-17, so
  ageing untouched). Data-movement, out of this tranche by the standing rule; routed, not acted on.

- 2026-08-20 — **Measured instance of the `git stash` drop defect this plan already tracks.** A `safe-doc-push.sh`
  run naming three doc files reported `✅ Pushed 241933d56e` and landed only TWO. The run began with
  `🛑 127 entries is extreme — quarantining current dirty tree into a named stash BEFORE the pull`; that quarantine
  swept this plan's then-uncommitted edits, and the isolated commit went ahead from the pre-edit version. Both the
  W4 todo annotation and the W4 Progress Log entry above were silently dropped — local and origin both sat at 402
  lines with zero `W4 alerting` hits. Caught only by grepping origin for the specific text after the ✅.
  **The push's own success message is not evidence that every `--files` entry landed** — verify per file. Re-applied
  from source rather than excavating 127 stashes. Direct evidence for
  `/plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`, which
  this plan carries as a P1.

- 2026-08-20 — **Grain auto-detection VERIFIED, not assumed** (the P0 says so explicitly) —
  `unified-trading-pm@c3a3e870f4`.

- 2026-08-20 — **Full-fleet dump RUN (runtime verification, not just unit tests) — and it re-points the effort's
  critical path.**

  Ran `derive_readiness.py` end-to-end under `instruments-service/.venv` against
  `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json`, grain `instrument_type`, 288 venues × 3
  modes = **864 rows**. This is the runtime verification the shipped code owed — the new `execution_instruction`
  leg renders its measured denominator on every row, and the dump-level coverage finding prints once as designed.

  **864-row total RECONCILED**: the dump reproduces the artefacts' quoted headline **exactly — ready 0 /
  not_ready 844 / unverified 20**, denominator 864, date 2026-08-19.

  **FINDING 1 — the stated critical path is wrong.** This plan and the coordinator both assert that T4's
  execution-instruction check is "the structural reason all 864 rows read `unverified`". Measured per-leg:

  | leg | ready | not_ready | unverified |
  | --- | ---: | ---: | ---: |
  | `strategy` | 24 | **840** | 0 |
  | `execution_transfers` | 0 | 768 | 96 |
  | `market_tick_data` | 109 | 470 | 285 |
  | `execution_instruction` | 0 | 0 | 864 |

  The rows are **`not_ready`, not `unverified`**, and rollup lets any `not_ready` dominate. With `strategy`
  failing on 840 of 844, closing the instruction leg entirely would move **zero** rows. The headline is gated by
  **strategy position-adapter coverage** (`position_read_mode_availability(venue).<mode> = none`, strategy-service
  — T3's repo), not by T4. Tracked as a P0 above; the coordinator should re-point before more effort is spent on
  the assumed edge.

  **FINDING 2 — the execution legs in this run are a floor, not a measurement.** The execution-service probe
  subprocess exited 1 (`No bucket configured for market_data/defi and no project ID available`), so all four
  execution-service legs reported `unverified=864`. The same probe SUCCEEDS single-venue — `--venue OKX-FUTURES`
  derives `execution_orders=ready` at PAPER and LIVE. Environmental, not absent capability. The dump degraded
  honestly (probe unavailable → `unverified`, never a silent pass), which is the design working, but the
  execution-leg counts must not be quoted as capability until fixed. Tracked as a P1 above.
  `tests/test_shard_universe_grain_detection.py`, 7 tests passing. The case that matters for the T2 handoff is
  the third: when T2 lands the `by_venue_instrument_type_data_type` KEY before landing data under it, a detector
  keyed on mere key-presence would flip to the fine grain and enumerate **zero** shard cells — every coverage
  figure silently collapsing while looking structurally fine. The shipped detector requires a non-empty venue
  block and correctly falls back, still reporting the real 2-tuple cells. Confirmed by test, not by reading.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

- 2026-08-20 — **Artefact ownership invariant CLOSED: 37 → 0 untagged claims, verified per-file in origin.**
  `unified-trading-pm@840d453409` (2 new readiness axes + Pendle baseline fix), `@09938ebebf` (execution-service
  probe root-cause fix + 28 owner tags), `@a80fa4f41b` (final 9 owner tags closing the ratchet to zero, baseline
  lowered to match). Every claim-bearing section in every one of the 7 client artefacts now carries a real
  `owner:` tag citing a doc verified to exist on disk. Detail already recorded against the W21 invariant todo
  above and in the standalone entries for each ship.

- 2026-08-20 — **W4: found a second already-fixed alerting defect (escalation-pool-exhaustion), corrected the
  stale issue doc rather than re-implementing.** `agent-orchestrator@78a9a02c` (2026-08-19) already decouples
  `_maybe_alert_pool_exhaustion` from `retry_queued_escalations` exactly as
  `escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18.md`'s own "Recommended fix" section
  specifies — its docstring cites the issue slug verbatim. Confirmed via 9 passing regression tests on current
  code (`test_drain_escalations_skips_retry_but_still_verifies_when_halted` +8 more). The issue doc's `status:
  open` and its P2 fix-todo were stale for shipped, tested work; flipped in place. Its P3 live-verify todo stays
  genuinely open — needs a real future exhaustion window's `journalctl` output this pass does not have; unit
  tests confirm the code path is reachable, they do not substitute for the live confirmation that todo asks for.

- 2026-08-20 — **W4/close-out: found and fixed a THIRD, genuinely new git-status-alerting defect** (distinct
  from the two above, which were already fixed) while verifying `git_status_red_nudge_false_positive_wrong_
  branch_comparison_2026_08_17.md`'s two ORIGINAL todos (confirmed already `[x]`, shipped 6 days prior) — its
  2026-08-19 addendum named a THIRD, still-open mechanism this pass then fixed.

  `server/worker_liveness/_git_alerts.py::maybe_nudge_on_red_repos`'s `ahead` branch fired with **no age gate at
  all**, unlike every sibling branch in the same function (`dirty` > 3600s via `dirty_oldest_mtime`, `behind` >
  600s via `not_clean_since`) — confirmed by direct code read matching the issue doc's own diagnosis exactly. A
  momentary `ahead=1` reading between a commit landing and its push (the normal two-pass ship flow every T5 ship
  this session has been running) could nudge on the very next ~5-min tick. Fixed: gate on `not_clean_since`
  sustained past 600s, matching this function's own local `behind`-branch precedent — deliberately NOT the
  separate 90-min `GIT_RED_SUSTAIN_S` used by the different-tier Slack-paging function
  `maybe_alert_git_staleness`, whose own `ahead` branch was already correctly sustained and needed no change.
  2 new regression tests added (`test_nudge_ahead_not_sustained_does_not_fire`,
  `test_nudge_ahead_sustained_fires_with_age`); file 26/26 passing, broader worker-liveness suite 103/103.
  **NOT YET LANDED, 2026-08-20** — ship failed on `dashboard/node_modules` missing `@vitest/coverage-v8` (environmental, unrelated to this change; exit 0 with nothing landed, caught by per-file origin verification, not by the exit code). Fix + 2 tests preserved locally AND backed up outside git (scratchpad/agent-orchestrator-backup/) since this session already measured local edits as fragile under contention. Needs `npm --prefix dashboard install` (or equivalent) before the next agent-orchestrator ship attempt — flagged as its own todo below since it will block ANY future ship to this repo, not just this fix.

- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, first audit pass): KEEP-NA, valid — Tranche 5 of the operator-slot-launched code-readiness series (same Launch-prompts mechanism; also owns the acceptance-test artefacts). Remaining open items are explicitly gated on a 2026-08-20 operator decision to wait for the state-fabric ledger plan before any artefact hand-edit (the 4 DOC re-derive todos + disclosure-standard extension + FROM-T1 API-surface regeneration), a VM-launch decision for 2 manifest-hygiene P2 residuals, and an AO-dispatch-queue item outside this tranche's direct control. None clears the whole-doc RECLASSIFY bar.

## Deferred work after 2026-08-20 (revised 2026-08-20, pre-compact — fully-resolved rows removed, evidence lives on
the todo checkboxes themselves; only genuinely-still-open items stay here)

| Item | State / why deferred | Blocked on |
| --- | --- | --- |
| 4 DOC "re-derive artefacts" todos | Not started — **operator decision 2026-08-20: wait for the ledger plan** (`/plans/active/state_fabric_artefacts_2026_08_20.md`), do not hand-edit | That plan landing its ledger-binding, or an explicit reprioritization |
| Disclosure-standard extension (2 sibling artefacts) | Not started — same operator decision (also a hand-HTML-edit) | Same as above |
| FROM-T1 API-surface regeneration | Same operator decision (also a hand-HTML-edit) | Same as above |
| `git stash push/pop` core fix | Not done — real work exists in `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md`, not yet landed | AO dispatch queue, not mine to force |
| Manifest-hygiene 4 residual P2 items | Cannot be done yet — 2 need a VM launch (`detect_manifest_divergence.py` OOMs locally on 14M+-row manifests) | A deliberate VM-launch decision |
| AO watchdog scheduled-timer wiring | Wiring itself is done (6/7 todos); sole remainder is re-running the install script on the central VM | Operator — needs VM SSH |
| `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` 2 verified fixes | Written, evidence-checked, ready to paste — see the dedicated `- [ ]` todo above | Pre-existing line-cap block (needs a split or a 5th `check_line_caps.sh` carve-out) |
| Post-phase codex audit, final gate | Gated on the 3 plan-conflict-parked artefact items above landing first | Same as those 3 |

**Recommended next**: none of the remaining items are quick wins — every one needs either the operator's ledger-plan
call, a VM-launch decision, or someone else's AO-dispatched work landing first. Nothing here is actionable by simply
spending more session time on it.

## Lessons carried forward

Moved verbatim to `/plans/active/code_readiness_t5_progress_history_2026_08_21.md` (parent at the 1000-line hard cap).
