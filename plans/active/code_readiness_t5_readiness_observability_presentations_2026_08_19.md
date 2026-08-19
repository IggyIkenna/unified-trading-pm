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

- [ ] [FROM-T2] P0. **You are NOT blocked on the coverage grain — it already landed. Re-run the dump.** Your
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

- [ ] [FROM-T2] P1. **Your readiness dump's `grain` field is mislabelled — the writer, not the file.** This is the
      `/plans/epics/system_readiness_master.md` § W3 `[DOC] P1` item, and it lands in a file this tranche owns, so
      T2 has not touched it. MEASURED: `plans/audit/results/readiness_pipeline_stage_per_shard_2026_08_18.json`
      declares top-level `grain: "instrument_type"` while all 864 rows carry only
      `['venue', 'asset_group', 'mode', 'pipeline_stage', 'leg_states']` — no `instrument_type` key on any row.
      Root cause is in `cursor-configs/skills/readiness-state-dump/scripts/derive_readiness.py:208`:
      `grain = detect_grain(coverage_payload)` reads the grain of the **coverage source** and then reports it as
      the grain of the **readiness rows**, which are built at `venue x asset_group x mode`. The two are different
      things. Suggested shape: emit `row_grain: "venue_asset_group_mode"` for what the rows actually are, and keep
      the source's grain under its own key (`coverage_source_grain`), so neither is silently claiming the other.
      Also worth a look while you are in there: 9 rows carry an EMPTY `venue` string (all `asset_group: sports`) —
      they come straight through from 9 blank-venue cells in coverage.json, which T2 is tracking separately.

- [ ] [FROM-T4] P0. **The per-venue execution-instruction-path check you are blocked on is BUILT — here is its
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

### W1 — readiness derivation and the state dump

- [ ] [BACKEND] P0. Derive a batch / paper / live state for EVERY venue with a code path, surfacing `unverified`
      honestly wherever a check does not exist. Epic definition-of-done item. Engine:
      `cursor-configs/skills/readiness-state-dump/`.
- [ ] [BACKEND] P0. Wire T4's per-venue execution-instruction check into the dump the moment it lands — this is what
      moves 844 `not_ready` rows off their structural blocker. Track the dependency; do not wait idle on it.
- [ ] [BACKEND] P0. Add the archetype capability axis across batch, paper and live to the dump. The artefacts mark
      it `planned — specified and not yet built`, so that axis reports `unverified` today. Consume T3's
      `/archetype-code-completeness` output rather than re-deriving it.
- [ ] [BACKEND] P0. Make credentials a first-class readiness dimension (W1 addition 2026-08-19).
- [ ] [BACKEND] P0. Make manual execution mode first-class alongside automated (W1 addition 2026-08-19).
- [ ] [BACKEND] P0. Reconcile the 864-row all-group total quoted in the artefacts (`ready 0 / not_ready 844 /
      unverified 20`) against §17's own table — the artefacts flag it as not reconciled.
- [ ] [BACKEND] P1. Resolve the per-venue and per-data-type cells that remain pending at the finer grain inside each
      readiness tree.
- [ ] [BACKEND] P1. Fix the tree gaps the artefacts name explicitly — Scroll and zkSync read `unverified — declared,
      never attempted`, and Plasma is `not a ChainKind member`. Consume T1's single chain SSOT; do not re-derive.

### Honest coverage — every shard, with a denominator

- [ ] [BACKEND] P0. Dump honest coverage per shard across the full shard universe, every figure carrying its
      denominator and date. Engine: `cursor-configs/skills/honest-coverage-dump/` reading the already-computed
      `coverage.json` — never re-derive the expected universe and never re-walk GCS.
- [ ] [BACKEND] P0. Re-run the dump at the finer grain the moment T2 lands `instrument_type` / `data_type` in
      `coverage.json`. The skill auto-detects grain from the payload — verify that, do not assume it.
- [ ] [BACKEND] P0. Report the 4-state capture ledger per shard (captured / expected-absent / attempted_failed /
      expected_unattempted) plus a not-expected section for tuples outside the Layer-1 expected universe.
- [ ] [BACKEND] P1. Close the remaining data types the artefacts mark pending — on-chain, sports odds, prediction
      and TradFi vendor datasets.
- [ ] [BACKEND] P1. Resolve the manifest-hygiene red findings. Evidence:
      `/plans/active/issues/manifest_hygiene_red_all_2026_08_17.md`, `/plans/active/issues/manifest_hygiene_red_all_2026_08_18.md`.
- [ ] [BACKEND] P1. Resolve the empty-reprobe disagreement finding. Evidence:
      `/plans/active/issues/empty_reprobe_disagreement_all_2026_08_17.md`.

### W4 — observability, alerting and auto-recovery

- [ ] [BACKEND] P0. Close the `dp_cron_did_not_fire` alert defects — the storm recurring on a stable revision, dedup
      state lost on redeploy, and the volatile dedup field. Evidence: the three
      `/plans/active/issues/dp_cron_did_not_fire_*` docs.
- [ ] [BACKEND] P0. Fix the escalation-pool-exhaustion alert being unreachable when halted. Evidence:
      `/plans/active/issues/escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18.md`.
- [ ] [BACKEND] P1. Verify every actionable alert that pages an OPEN gets a ✅ CLOSE bookend in-channel. SSOT:
      `/codex/04-architecture/agent-orchestrator-alerting.md`.
- [ ] [BACKEND] P1. Complete the E2E wiring reachability audit. Evidence:
      `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md` (11 open).
- [ ] [BACKEND] P2. Fix the SIT stamp-dispatch 503 false positive. Evidence:
      `/plans/active/issues/sit_stamp_dispatch_503_false_positive_2026_08_17.md`.

### W21 — the presentation artefacts (the acceptance test)

- [ ] [DOC] P0. Re-derive `platform-architecture.html` from measured state. Every remaining marker must be live or
      one of the five allowed pending states.
- [ ] [DOC] P0. Re-derive `platform-external-api-walkthrough.html` — the heaviest artefact by gap count (28
      `unverified`, 27 `pending`, 17 `planned`, 17 `partial`, 14 `not yet`, 6 `missing`, 5 `not built`).
- [ ] [DOC] P0. Re-derive `strategy-service-deep-dive.html` (51 `unverified`, 15 `partial`) against T3's output.
- [ ] [DOC] P0. Re-derive `strategy-service-walkthrough.html` (23 `partial`) against T3's output.
- [x] [DOC] P0. Verify the invariant the epic sets — **every claim-bearing artefact section maps to a tracked
      item**. Build the check; it has already failed once, measurably. — `unified-trading-pm@7b2dd29aaa`.
      `scripts/plan-hygiene/check_artefact_claim_ownership.py`, wired into `run_hygiene_sweep.sh`. Measured
      2026-08-20 over the 7 artefacts: 84 top-level sections, 83 claim-bearing, **37 carrying no `owner:` tag**,
      189 open markers (st-part + st-plan + ev-check + ev-assumed), 55 closed. The invariant is confirmed FAILING
      and is now ratcheted — both counts can only go down. Owner resolution reads the tag's `title` attribute (the
      machine-readable doc path) before the visible label; label-only resolution produced 3 false violations on
      this corpus, so the checker was corrected before seeding rather than baselining the lie.
- [ ] [DOC] P0. Extend the same disclosure standard to the four sibling client artefacts the 2026-08-18 audit found
      violating it and which no remediation plan covers — `carveout-engineering.html` and
      `ODUM_Elysium_Phase2_Update_2026-07-24.html` alongside the two already in scope. Evidence:
      `/plans/active/client_artefact_remediation_2026_08_18.md`,
      `/plans/active/client_artefact_remediation_nickai_2026_08_18.md`.
- [ ] [DOC] P0. Confirm no figure outruns its measurement — every number carries date and denominator, or says
      pending. Epic definition-of-done item.

### W19, W20 — corpus and automation

- [ ] [AGENT] P1. Run the corpus audit — nothing relevant left un-folded, nothing stale left believed. Epic
      definition-of-done item. Use `/plan-reconcile` and `/docs-reconcile`.
- [ ] [AGENT] P1. Fix the docs-reconcile findings and the remaining broken links. Evidence:
      `/plans/active/issues/docs_reconcile_findings_2026_08_17.md`,
      `/plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md`.
- [ ] [AGENT] P2. Land the AO watchdog scheduled-timer wiring. Evidence:
      `/plans/active/issues/ao_watchdog_scheduled_timer_wiring_2026_08_17.md`.

### Infrastructure defects that cost other agents time

- [ ] [BACKEND] P1. Fix `git stash push/pop` silently dropping content under high branch velocity — this defect
      costs every tranche real work. Evidence:
      `/plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`.
- [ ] [BACKEND] P1. Add the retry safety net for `main-backmerge-to-ldr` on non-PM repos. Evidence:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md`.
- [ ] [BACKEND] P1. Fix the `unified_trading_ci` FF-pull cron branch-override gap. Evidence:
      `/plans/active/issues/unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md`.
- [ ] [BACKEND] P3. Fix the git-status red-nudge false positive from the wrong branch comparison. Evidence:
      `/plans/active/issues/git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md`.

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's 433-doc allocation to zero open todos or an explicit
      `BLOCKED-*` tag. This is the largest tail of the five — expect AO, CI and plan-hygiene work.
- [ ] [AGENT] P0. Post-phase codex audit for every contract changed.
- [ ] [AGENT] P0. **Final gate for the whole effort** — confirm all four artefacts carry no `pending`, `planned`,
      `partial`, `not built` or `unverified` marker outside the five allowed states, and that every number carries
      its denominator and date.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

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
  Not yet shipped (in progress this session).

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

- 2026-08-20 — **Grain auto-detection VERIFIED, not assumed** (the P0 says so explicitly). Not yet shipped.
  `tests/test_shard_universe_grain_detection.py`, 7 tests passing. The case that matters for the T2 handoff is
  the third: when T2 lands the `by_venue_instrument_type_data_type` KEY before landing data under it, a detector
  keyed on mere key-presence would flip to the fine grain and enumerate **zero** shard cells — every coverage
  figure silently collapsing while looking structurally fine. The shipped detector requires a non-empty venue
  block and correctly falls back, still reporting the real 2-tuple cells. Confirmed by test, not by reading.
