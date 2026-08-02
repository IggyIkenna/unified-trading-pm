---
doc_type: plan
title: Sports satellite AO batch 6 — orphans created or missed by batch5's own 2026-07-26 pass
summary: >-
  Sixth AO-dispatch batch for sports, produced by an `/ag-closeout-audit sports` run later on 2026-07-26 (autonomous
  mode, operator away). batch5's Phase-1 snapshot was taken earlier the SAME day; its own execution then (a) split
  `sports_features_layer_findings_sweep_2026_07_18.md` into 3 parts, structurally orphaning 55 open todos whose covering
  citations still point at the pre-split filename, and (b) spun off 6 new sports issue docs that batch5 only names as
  "filed as a follow-up" — a mention, not dispatch. Three further docs batch5 never cited at all were also found. 11
  docs classified orphaned (7 carrying AO-eligible bounded work, 4 purely operator/design-gated); Phase 3's conflict
  check cleared 9 into todos below, refuted 1 as a verbatim duplicate of an existing draft todo, and left 4 items in the
  Deferred sections. The 16 items batch5 itself deferred are NOT re-surfaced here — `batch5_finalize` todo 2 already
  owns their re-check and explicitly names `batch6` as the destination for any that clear.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, instruments-service, market-tick-data-service, features-service, deployment-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-6, satellite-docs, line-cap-split-orphans]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (second run of the day, autonomous mode — operator away and unreachable).
  Phase 0 discovered the 17-doc covering set; Phase 1 classified the 109 sports-tagged docs, running the per-doc read
  inline (no Workflow/Agent tool was available in this environment — stated plainly, not silently skipped) and leaning
  on batch5's own same-day recorded per-doc adjudications for the 41 docs it had already classified rather than racing
  `batch5_finalize` todo 2; Phase 3 ran the documented conflict-check over every candidate before drafting.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 6 — post-batch5 orphans

> **✅ `status: active` — dispatched.** This banner previously said `status: draft — NOT dispatched`, stale ever since
> the frontmatter was flipped `active` (found + corrected 2026-07-27 while using this doc as the format template for
> `sports_satellite_ao_dispatch_batch7_2026_07_27.md`). Its companion,
> `/plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26_finalize.md`, is machine-gated via
> `depends_on`/`gate_on_depends: true` regardless of its own `status`.

> **Why a batch6 exists one day after batch5.** `batch5_finalize` todo 2's own text names the destination: _"extract it
> as a new tracked todo in a follow-up `batch6`"_. batch5 is `status: active`, mid-dispatch, and already at its
> 1000-line hard cap — its Deferred items cannot be folded back into it, and the orphans below did not exist when its
> Phase-1 snapshot was taken.

> **2026-07-28 operator-decisions pass.** Of the 4 originally purely-operator/design-gated docs this batch classified
> (see `summary:` above), 3 are now RULED and moved from the Deferred sections into `## Todos` as todos 10-12: the GCS
> soft-delete retention decision, the xG-column build-vs-prune decision, and the odds_api-ownership-routing decision
> (that last one's actual ruling + task lives in its own source issue doc, one of this same pass's assigned files — todo
> 12 here is a pointer, not a duplicate). The 4th (`ml_service_sports_clv_training_pipeline_never_functional`) and the
> two process-level Deferred bullets (todo-7 generalisation, tranche ownership) remain genuinely gated — see their
> entries below for why. The naming-migration plan-reclassification question inside todo 8 (step 3) also stays
> `[OPERATOR]`, reviewed and reaffirmed, not resolved by the general theme (see that todo's own note).

## Cross-todo file-collision check (done before finalizing, per the skill)

Same-priority todos in one plan run concurrently by default, so same-priority todos must touch distinct files.

| priority | todos        | files touched                                                                                                                                     | collision                              |
| -------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| P1       | 1, 2, 4, 7   | part2 / part3 / capture-outage doc + mtds / the 5 sports `*_finalize` plans                                                                       | none                                   |
| P2       | 3, 8, 9, 10  | `launch-features-vm.sh` + part3 / naming doc + its parent plan / `native_ao_extract` / deployment-service terraform                               | none                                   |
| P3       | 5, 6, 11, 12 | `instruments-service/scripts/` / `features_service/sports/` (todo 6) / `features_service/sports/` (todo 11, xG) / no file (todo 12, pointer only) | **todo 6 vs todo 11 — see note below** |

**One deliberate ordering dependency, handled by priority rather than `sequential: true`** (which would needlessly
serialise all 9): todo 3 (P2) flips a checkbox inside part3, which todo 2 (P1) also edits. P1 drains before P2, so todo
2 lands first. Todo 2's text is explicit that it must LEAVE the § Y checkbox open and annotate it as owned by todo 3.

**Second potential collision, flagged 2026-07-28 when todos 10-12 were added by the operator-decisions pass**: todo 6
(the `pd.NA`-idiom sweep) and todo 11 (the xG-columns build-or-prune ruling) both touch `features_service/sports/`, and
todo 11's implementation work may land in the same `multisource_xg_calculator.py` todo 6's own text already cites as the
one confirmed-fixed site. Both are P3 (concurrent by default). If both are picked up in the same window, whichever
worker starts SECOND should `git pull --ff-only` immediately before editing and re-check for an overlapping in-flight
diff on `multisource_xg_calculator.py` before touching it — not a `sequential: true` (that would needlessly serialise 4
otherwise-independent P3 todos over one soft file-overlap risk).

## Todos

- [x] ✅ [DOC] P1. **Reconcile `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`'s 24 open
      checkboxes against their real current state — and neutralise the reversed-casing hazard in its § K block FIRST.**
      This doc was created 2026-07-26 by batch5's own § A2 line-cap split of the 1,843-line parent; every covering-plan
      citation still names the PRE-split filename, so §§ G-N's 24 open todos are structurally uncovered.
      **Safety-critical sub-part, do this before anything else in this todo**: § K1/§ K2 still carry open todos reading
      _"DIRECTION CORRECTED — emit UPPER, not lower"_ and _"QG assertion: sports `data_type` ∈ the UAC **UPPER-case**
      sports vocabulary (per K0-DECISION (b))"_, citing the operator's 2026-07-18 K0-DECISION. That decision was
      **REVERSED 2026-07-23** — `sports_consolidated_closeout_2026_07_19.md`'s Canonical-target section states
      _"data_type = LOWER-case everywhere for sports — FINAL, reconciled 2026-07-23"_ and _"This REVERTS Track C's K1/K2
      work below"_. A worker picking up part2 § K1 today ships the WRONG casing direction — **this exact failure has
      already happened once**, recorded in
      `/plans/archive/issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`. Annotate
      every § K todo with a dated `⛔ SUPERSEDED 2026-07-23 (lowercase revert)` marker pointing at the closeout's Track
      C revert todo; do NOT delete them (they are the historical record of what shipped and why it is being undone, the
      same treatment Track C's own K1/K2 lines got). Then, for each of the remaining § G-N open todos, classify against
      evidence and record the verdict inline: superseded by a later dated section in this same doc (§ G-RESOLVED, §
      G-ops, § H-UPDATE, § L-VERIFIED, § M-FIXED are all present and dated) → flip `[x]` citing that section; owned by a
      covering plan (§ J's staleness-budget item is shipped as `unified-trading-library@fd87daa1` per the closeout's
      Track H, and its deployment-api mirror is already a drafted todo in
      `sports_consolidated_native_ao_extract_2026_07_25.md`) → annotate with the owner, do not flip; genuinely open →
      leave `[ ]` with a one-line reason. Repo: unified-trading-pm. **Done when**: all 24 checkboxes carry either an
      `[x]` with cited evidence, an owner annotation, or a stated reason they remain open; every § K todo carries the
      superseded-direction marker; and the doc stays under the 1,000L hard cap (it is ~600L, so there is room — verify
      with `bash scripts/plan-hygiene/check_line_caps.sh` before committing). Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`. — DONE:
      `unified-trading-pm@d20df1288`. All 16 checkboxes still open at pickup time (8 of the original 24 had already been
      flipped by an intervening `docs(plans): stale-checkbox correction pass` commit, `77766e441`) classified: 9 flipped
      `[x]` with cited evidence (round-writer-fix duplicate, watchdog-artifact lesson codified into
      `async-wait-and-poll-discipline.md`/CLAUDE.md, § H false-`attempted_failed` self-heal, singleton-bypass
      root-caused as by-design + oversubscription damage closed via the registry, enrichment-fleet relaunch-on-429 loop
      closed, § K0 ASK answered by K0-DECISION, RelaunchPreemptedVm re-derive superseded by § M-FIXED, full-force
      FIXTURES run superseded by the surgical script + independently-verified live round/competition_phase state); 7
      left open with a one-line reason (2 owned by Track V's still-open catalogue re-roll, 4 genuinely unresolved —
      error-text softening, residual-61-rows re-verification, mid-flight fleet re-throttling, the surgical-filler
      process lesson never codified — plus the MVP-denominator gap on `emit_empty_gaps_for_entity`). Safety-critical §
      K1/K2/K3 sub-part: added an explicit `⛔ SUPERSEDED 2026-07-23 (lowercase revert)` marker to all 8 already-flipped
      § K checkboxes (they carried an "already covered by" citation but not the requested marker text). Doc stays at
      752L, under the 1,000L cap (`check_line_caps.sh` verified clean).

- [x] ✅ [DOC] P1. **DONE — `unified-trading-pm@<see plan-flip commit>`.** Reconciled
      `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`'s open checkboxes (§§ O-AA) against real
      current state. **Count correction found at pickup**: only **29**, not 31, were open — same class as todo 1's
      finding, an intervening `docs(plans): stale-checkbox correction pass` commit (`77766e441`) had already flipped 2
      before this todo ran; verified via `git log` on the file. Classified all 29: **25 flipped `[x]`** citing the
      terminal-state table (§ Q/§ T/§ W's own already-flipped asks) plus the design/measurement sections that answered
      each earlier ask in full (§ O's catalogue-rebuild hypothesis test, § P/P-SIZING/P-ERA's derive-then-fetch design —
      all superseded by § Q's shipped script — § R's entity repoint, § S/§ V/§ X's features re-run — superseded by
      Z-FIXED's later consolidation into Track F — § T/§ U's decision items citing the closeout's ANSWERED-2026-07-20
      operator decisions verbatim, verified by reading Track V directly); **2 owner-annotated, left open** (§ R's
      `[DIAG] P0` ~9-consumer audit + its R-FIXED duplicate, owned by the closeout's Track E, confirmed still open
      there); **1 left open as genuinely unresolved** (§ R's `[PROCESS] P1` entity-migration rule — checked
      `codex/12-agent-workflow/` and `codex/04-architecture/` for an existing codification, found none; not batchable,
      same class as this plan's own todo 7 Deferred item); **1 left open per instruction** (§ Y, annotated
      `owned by     batch6 todo 3`). **§ Z correction**: the plan's own text asked to "leave § Z's `[DATA] P3` OPEN and
      annotate it as parked" — but that checkbox was ALREADY `[x]` SUPERSEDED in the doc at pickup time (line ~781,
      resolved via `autonomous_session_operator_decisions_2026_07_25.md` entry #15, "deleted as redundant, not
      executed"), so this plan's own Deferred-section premise (a live mechanism conflict) was stale before this todo
      even ran — no action taken since there was no open checkbox to annotate; noted here rather than silently ignored.
      `check_line_caps.sh` clean (879L, no new violations — `1 pre-existing violation(s), within baseline (17)`).

- [ ] [CODE] P2. **Fix `launch-features-vm.sh`'s post-backfill hint — it names a bucket that 404s, and that already
      produced a 20-minute false-stall reading.** The launcher's closing instructions tell the operator to run
      `rebuild_manifest_from_canonical_paths('features-sports-sports-central-element-323112', ...)`. That bucket does
      not exist: the hint interpolates `<family>-<asset_group>` and drops the `-prd-` env segment. The real name is
      `features-sports-prd-central-element-323112`, and the data prefix in the hint is wrong too — objects live under
      `sports_features/`, not `features/by_date/`. Resolve the bucket via
      `resolve_bucket_name(cloud="gcp",     kind="features", asset_group="sports")` and never string-interpolate an
      env-split bucket name (CLAUDE.md § Writing STORAGE code; QG 5.69). **Why this is worth a todo and not a typo
      fix**: the source finding records that a watchdog armed on the hinted bucket read `shard_days=0` for 20 minutes,
      indistinguishable from a genuinely stalled backfill — a 404 bucket does not error in a `| wc -l` pipeline, it
      silently returns zero forever. This is the inverted form of the async-wait rule 1a hazard
      (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`). **ALSO swap the function itself (added 2026-07-30,
      `rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` todo 4's corpus sweep)**:
      `rebuild_manifest_from_canonical_paths()` wholesale-REPLACES the target bucket's whole manifest index on a
      prefix-scoped call — fixing only the bucket/prefix strings turns this hint from a harmless 404 into a LIVE wipe
      risk the moment the bucket name resolves. Swap to the additive `merge_manifest_from_canonical_paths()` (same
      module; `prefix` is required, not optional, on the additive sibling) in the SAME edit — do not ship the
      bucket/prefix fix without the function fix. Repo: deployment-service. **No `[OPERATOR]` gate needed
      (`task_template.md` finding O justification)**: this todo names a VM launcher (`launch-features-vm.sh`) and so
      trips the `check_delete_vm_launch_gating.sh` soft pre-filter, but it **launches no VM, writes no GCS object and
      deletes nothing** — the entire change is to the launcher's printed post-backfill HINT TEXT (a Python bucket-name
      string it echoes for the operator to copy), shipped as source via the normal quickmerge path, and its done-when is
      a `quality-gates.sh` run plus a checkbox flip. Safe-idempotent by construction. **Coordination**: todo 2 (P1,
      drains first) leaves part3's § Y checkbox open and annotated for you — flip it as part of THIS todo's evidence,
      and do not make any other edit to part3. **Done when**: the hint resolves the bucket and prefix through
      `resolve_bucket_name`/the real `sports_features/` prefix AND calls `merge_manifest_from_canonical_paths()` (not
      the wholesale-replacing sibling), a `quality-gates.sh` run is green on deployment-service, and part3's § Y
      checkbox is `[x]` with the shipping sha. Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` § Y.

- [x] ✅ [DATA] P1. **`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` carries
      `assigned_vm: planning` but ZERO checkboxes — convert its 3 prose next-steps into tracked todos, then execute the
      2 bounded ones.** — unified-trading-pm (this commit, todo doc edit), market-tick-data-service@6ac4e60a (DeFi check
      script). Added the `## Todos` section (verbatim text preserved) to the source issue doc; item 1 left unchecked
      `[OPERATOR]` per Step 2 with the DEPLOY-already-satisfied note; item 2 executed fresh — DeFi consolidator
      confirmed HEALTHY, measured verdict NOT AFFECTED (Window A 10/10 days before fix vs Window B 9/10 days recent,
      both near-full coverage); item 3 confirmed already shipped by a prior slot (`market-tick-data-service@6f546b88`, 7
      unit tests, QG green). This doc is marked for orchestrator dispatch (`assigned_vm: planning`,
      `execution_scope: orchestrator-agent`) yet `regen_backlog_from_plan.py` derives todos from checkboxes, so its work
      is structurally invisible to the backlog — it can never be dispatched in its current shape. Step 1: convert the
      three items under "Recommended decision / next steps" into properly-tagged `- [ ]` checkboxes under a `## Todos`
      heading, preserving their text verbatim. Step 2: leave item 1 (the ~1-month-gap backfill decision) as an
      `[OPERATOR] P0` checkbox — it is a credits/priority call, explicitly not a worker one; note in it that the DEPLOY
      half of that item is already satisfied by the doc's own dated correction banner (_"DEPLOY CONFIRMED (2026-07-26,
      directly verified, not inferred)"_, image `f6001`/`410d756` digests + a log-inspected post-deploy execution with
      zero `DATA_NOT_AVAILABLE`), so only the backfill fork remains. Step 3: execute item 2 — verify whether DeFi's
      same-day capture was also blocked by the same `TickDataHandler._check_early_exit` future-date guard (the removed
      design comment said _"DeFi: immediate"_ too, and the fix `market-tick-data-service@410d7569` put DEFI on the
      relaxed branch, so the question is whether historical DeFi capture was starved before it landed). **Check the defi
      manifest consolidator's CURRENT health first, do not assume it is still down** — the source doc could not measure
      DeFi because `market-data-tick-defi-prd-central-element-323112`'s index raised `ManifestConsolidatorStaleError`
      (blob age 2204s > 120s) at the time. Compare a recent 10-day window against the 10 days before the fix,
      manifest-only, no GCS walk (single-walk discipline). Step 4: execute item 3 — add an explicit
      consecutive-non-422-failure counter to `odds_api_adapter.py::_run_league_fetch_loop`, which today catches
      `aiohttp.ClientResponseError` and `continue`s with no counter, no re-raise and no signal to the caller. Repos:
      market-tick-data-service, unified-trading-pm. **Done when**: the doc has a `## Todos` section whose checkboxes
      cover all 3 items; item 1 is an unchecked `[OPERATOR]`; item 2 is answered with a measured verdict (affected / not
      affected, with the two window figures cited) or explicitly marked blocked with the consolidator's re-measured
      state; item 3 is shipped with unit tests and `quality-gates.sh` green. Source:
      `issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`.

- [x] [SCRIPT] P3. ✅ **DONE 2026-07-28 — instruments-service@696921d3, this was a stale duplicate of the source issue
      doc's own todo (never flipped here).** Full per-script audit + the one genuine gap found
      (recover_fixtures_from_truthset.py::_write_per_league_parquet, fixed) — see
      /plans/archive/issues/sports_player_stats_empty_write_followups_2026_07_26.md (archived, resolved) for the
      complete per-script verdict list. quality-gates.sh --no-fix: 5009 passed, 0 failed. ~~Audit
      `instruments-service/scripts/` for the missing "refuse to write an empty/0-row result" guard that caused the
      player_stats empty-write incident.~~ Source: `issues/sports_player_stats_empty_write_followups_2026_07_26.md`
      (`[SCRIPT]` item). **Note**: that doc's sibling `[OPERATOR] P2` item (enabling GCS object versioning / soft-delete
      retention on the sports prd buckets) is deliberately NOT extracted here — it is an infra spend decision, see the
      Deferred section.

- [x] ✅ [REVIEW] P3. **DONE — `features-service@06a98496`.** Swept every `= pd.NA` initialisation site under
      `features_service/sports/` (`grep -rn "pd\.NA" features_service/sports/`, 14 hits across 9 files) and verdicted
      each: - `season_context.py:255` / `writer.py:157`'s comment — **NOT a dtype risk, no change.** Already
      independently verified 2026-07-30 in
      `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md`'s own sibling `[REVIEW]` item: every
      one of the 20 `SEASON_CONTEXT_COLUMNS` has a real, grep-confirmed assignment site. Spot- re-read this pass:
      unchanged since that verdict — no new action. - `goal_timing.py:301` — **genuinely never-filled → FIXED.**
      `early_goal_rate_*`/`late_goal_rate_*` (via `_derive_rates`) and the bucket/situational copies are only
      conditionally overwritten when their source columns are present in the input; when absent, the `pd.NA` pre-fill
      survives to return. Converted to `np.nan`. - `league_calculator.py:78` — **genuinely never-filled → FIXED.**
      `compute_league_features` (a live registered feature builder, `tracking/feature_builder_registry.py:66`) only ever
      assigns 5 of the 29 `LEAGUE_COLUMNS` (position/points-pct); the other 24 (attack/defense strength, goal metrics,
      win/draw/loss rates, home/away splits, relative strength) are NEVER computed by this entry point at all — always
      `pd.NA` (same class as the original 21 dead xG columns). Converted to `float("nan")`. - `venue_context.py:171` —
      **genuinely never-filled → FIXED.** Several numeric columns (`home_venue_*` stats, `away_cumulative_travel_km`,
      `*_days_since_last_match`, `is_evening_kickoff`, `is_midweek_match`, and the direct-copy columns) are only
      conditionally overwritten when their source column is present. Converted to `np.nan`. -
      `xg_decomposition_calculator.py:442` — **genuinely dtype-risk → FIXED (different mechanism, same root cause).**
      The per-fixture exception-handler fallback defaulted a failed fixture's row to `pd.NA`; confirmed empirically
      (`pd.DataFrame(rows)` with mixed `pd.NA`/float rows) that this upcasts the WHOLE column to `object` dtype for
      every fixture in the batch, not just the failed one, whenever `pd.DataFrame(rows)` mixes it with a successful
      fixture's real float values. Converted to `float("nan")`. - `relative_context_calculator.py:132` — **NOT a dtype
      risk, no change.** The `pd.NA` pre-fill is unconditionally and fully overwritten by the `METRIC_FAMILIES` loop for
      every one of the 60 `RELATIVE_CONTEXT_COLUMNS` before `out` is ever returned — a dead pre-fill, never
      observable. - `bucketed_features_calculator.py` (2 sites) — **NOT a dtype risk, no change.**
      `BUCKETED_FEATURES_COLUMNS` are genuinely categorical/string bucket labels (e.g. `"3-4"`, `"low"`) — `object`
      dtype is the correct, intended dtype for these columns, not an upcast artifact. `quality-gates.sh` green
      (sentinel-verified at `06a98496`). Repo: features-service. Source:
      `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md` (`[REVIEW]` item). **Note**: that
      doc's sibling `[OPERATOR/DESIGN] P3` item (decide which of the 5 unfilled xG column groups to build vs prune) is
      deliberately NOT extracted — the doc itself stops at diagnosis per the dispatch-scope rule.

- [x] ✅ [DOC] P1. **DONE — `unified-trading-pm@1e0399d6e`.** Added the missing source-doc-archival todo to the 5 sports
      `*_finalize` plans — the omission is why a CI gate had to auto-remediate 11 docs at 02:57Z today.**
      `task_template.md` § 4's finalize-plan rule has three parts: reconcile source-doc checkboxes, re-check deferred
      items, archive **the plan**. Nothing archives the SOURCE docs the batch drove to terminal status. Concretely,
      `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md` todo 1 says _"Only flip a doc's `status` to
      `resolved` if it genuinely reaches 0 open todos"_ — flipping a doc to `resolved` while it sits in
      `plans/active/issues/` is exactly what `check_terminal_status_archived.py` HARD-fails on. So the finalize plan, as
      written, creates the hygiene violation, and today the `plan_health` gate's own remediation
      (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545) archived all 11 rather than any plan owning
      it. Added a new todo — placed immediately AFTER each plan's own reconciliation todo (todo 1), not appended at the
      end, since the archival must follow directly on the heels of the status flip to close the actual violation window;
      the deferred-recheck and final-archive-the-plan todos shifted down and their internal cross-references (e.g. "todo
      2 above") were renumbered to match — to all 5 sports finalize plans:
      `sports_satellite_ao_dispatch_batch{2,3,4,5}_*finalize*.md` and
      `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` (this last one's todo 1 flips checkboxes back into
      one parent doc rather than many small source docs, so its new todo is tailored to note the expected-no-op case
      explicitly). Each new todo reads, in substance: archive every source doc the reconciliation todo drives to
      `status: resolved`/`complete` (re-verifying 0 open todos + a genuine resolution banner first), in the same commit
      as the flip, so `check_terminal_status_archived.py` never sees a terminal doc in `plans/active/`. Repo:
      unified-trading-pm. Verified: `bash scripts/plan-hygiene/check_line_caps.sh` clean on all 5 (104-125L, well under
      the 500L soft cap); `check_reference_paths.py` shows no new hit for any of the 5 filenames (baseline unchanged,
      162/941). `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` does NOT report 0 hard failures corpus-wide — it
      shows 3 pre-existing hard failures, confirmed via a stash-and-rerun on a clean LDR HEAD to be byte-identical with
      and without this change: (1) 2 already-`resolved` DeFi issue docs
      (`defi_maker_vault_share_price_29day_gap_2026_07_26.md`, `defi_mev_events_pagination_gap_2026_07_28.md`) sitting
      unarchived in `plans/active/issues/` — the exact same systemic gap this todo fixes for sports, corroborating the
      Deferred section's already-parked "generalise workspace-wide" recommendation below, not a new finding; (2) 1
      unrelated AG-closeout-linkage orphan (`solana_address_primitives_duplicated_across_mtds_handlers_2026_07_28.md`,
      `asset_group=[defi]`, created today by other concurrent fleet work); (3) `assigned_vm:NA` corpus size grew 3 docs
      / 2 todos past its ratchet baseline (388 vs 385, 1410 vs 1408 — ambient fleet backlog with its own designed
      remedy, `/na-eligibility-audit`). None of the 3 touch sports or any of the 5 files this todo edited — verified
      none of my edits caused a new violation on any of the 4 checks the sweep runs that DO relate to plan content (line
      caps, reference paths, frontmatter, todo format all pass). `quality-gates.sh` (the actual per-repo ship gate,
      which does NOT invoke `run_hygiene_sweep.sh`) is green on this commit. Source:
      `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2 (the "one durable gap this leaves"
      note — filed there explicitly as _"a small authoring change, not a decision"_). **Scope guard honored**: did NOT
      edit `plans/active/task_template.md` § 4 or the codex rule to make this workspace-wide — generalising the
      authoring rule to every AG's finalize plans stays parked for the operator (see Deferred; the 2 DeFi docs above are
      fresh supporting evidence for approving that generalisation).

- [x] ✅ [DOC] P2. **DONE 2026-07-30 (`/plan-reconcile` autonomous sweep) — all three steps closed, doc archived to
      `/plans/archive/issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md`.** Evidence,
      each measured this run, not inherited: **step 1** already flipped at
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s `[DATA] P1` line citing `features-service@b03a6de4`;
      **step 2** — this todo's own verification command was RUN:
      `git -C features-service merge-base --is-ancestor 0ded2449 origin/live-defi-rollout` exits 0 (subject
      `feat(sports): migrate ODDS_COLUMNS to the decided naming scheme`), and the parent plan's matching
      `odds_columns.py` / `ODDS_COLUMNS` migration todo is already `[x]`, so the sha is CONFIRMED, not assumed; **step
      3** — the `assigned_vm` re-designation question the paragraph below reserves for the operator was answered: the
      target doc's own second `[OPERATOR]` todo records "Operator-ruled 2026-07-29 (interactive decision session):
      formalize via the satellite …" and `unified-trading-pm@fcfa0c97b` closed the doc on that ruling
      (`status: resolved`, 0 open todos). The paragraph below is retained verbatim as the original instruction/reasoning
      — it is history now, not an open gate. **Close out
      `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` — 2 of its 3 prose steps are now
      satisfied by shipped commits.** This doc has zero checkboxes and expresses its remaining work as a 3-item prose
      "Recommended next step" list (the confirmed prose-only trap). Step 1 (flip
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s todo 2 for the shipped per-bookmaker decimal-odds
      compute) was executed 2026-07-26 by `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s `[DATA] P3` todo, citing
      `features-service@b03a6de4`. Step 2 (decide whether to commit the uncommitted todo-4 features-service rename diff
      that was sitting in slot 3's worktree) appears to have landed as `features-service@0ded2449` — batch2 and batch5
      both treat that sha as the shipped ground-truth naming migration, batch5's slot-10 todo having re-derived its
      125-entry old→new mapping positionally from that exact diff. **Verify this, do not inherit it**: this audit could
      not run `git log` against sibling repos (worktree isolation), so confirm with
      `git -C <features-service> merge-base --is-ancestor 0ded2449 origin/live-defi-rollout` and a spot-read of
      `odds_columns.py` before citing it. If confirmed: flip the parent plan's todo 4 `[x]` with the sha, record steps 1
      and 2 as resolved in this doc, and leave step 3 — whether the parent plan should stay `assigned_vm: NA` /
      LOCAL-only now that cross-repo migration code has landed against it piecemeal — as an explicit unchecked
      `[OPERATOR]` item, since re-designating a plan's execution track is the operator's call under CLAUDE.md's
      plan-destination HARD RULE. **Reviewed 2026-07-28 (operator-decisions pass) — genuinely left `[OPERATOR]`, not
      resolved by the general backfill/completion theme.** The theme's bullets (full backfills, cost tolerance,
      unpause/pause, adapter completion, live-probing scope) are about DATA/PIPELINE execution calls; whether to flip a
      plan's `assigned_vm` from `NA` to `planning` is a distinct WORKSPACE-GOVERNANCE decision that CLAUDE.md's
      plan-authoring HARD RULE requires an explicit operator ask for regardless of subject matter ("Default is human
      (`assigned_vm: NA`) unless the operator explicitly says otherwise") — the theme does not speak to it either way,
      so it stays a real open question for step 3, not a stale gate. If NOT confirmed, stop and record what you measured
      rather than flipping anything. Repo: unified-trading-pm. **Done when**: the doc carries a `## Todos` section with
      steps 1-2 `[x]` (or an explicit measured statement that `0ded2449` is not merged) and step 3 as an unchecked
      `[OPERATOR]` item, and the parent plan's todo 4 matches whatever was actually measured.

- [ ] [DOC] P2. **Cross-link the rebuild-delta todo in `sports_consolidated_native_ao_extract_2026_07_25.md` to its real
      source issue doc.** Phase 3's conflict check found that
      `issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md`'s sole
      genuine open todo (`[VERIFY] P2` — reconcile the post-07-13 rebuild delta, `PLAYER_VALUES` −10,934 / `ODDS` −3,180
      captured cells vs the 2026-07-12 verified state, via a per-key manifest-vs-GCS diff, to determine
      phantom-correction vs data loss) is ALREADY claimed verbatim — same figures, same mechanism, same done-when — by
      `sports_consolidated_native_ao_extract_2026_07_25.md`'s own `[VERIFY] P2` Track-S2 todo. **No competing todo was
      drafted for it** (the skill's clear-duplicate branch). But that todo cites
      `Source:     sports_consolidated_closeout_2026_07_19.md:937-941`, not the issue doc that actually tracks the
      finding — which is exactly why a citation-grep on the issue doc's own basename returned zero hits across all 17
      covering plans and it read as an orphan. Add the issue doc to that todo's `Source:` line and to the plan's
      `related:` frontmatter, and add a one-line pointer in the issue doc back at the owning todo. Repo:
      unified-trading-pm. **Done when**: the issue doc's basename appears in
      `sports_consolidated_native_ao_extract_2026_07_25.md`, the issue doc names its owner, and
      `bash scripts/plan-hygiene/check_reference_paths.py` reports no new violations. **Do not** execute the diff itself
      — it belongs to the existing todo, which is `status: draft` pending the same operator review as this plan.

- [x] ✅ [INFRA] P2. **DONE 2026-07-30.** RULED 2026-07-28 (operator-decisions pass, applying the general theme:
      recurring cost here is expected to be modest storage spend and "cost under $100 is not a concern" + prefer full
      protection over an all-or-nothing risk) — retagged away from `[OPERATOR]`, moved out of Deferred. Enabled a
      **bucket-level soft-delete retention window** (not full object versioning — matches the reversibility mechanism
      already standardized elsewhere in this workspace, e.g. the `gcs_bucket_soft_delete_retention_seconds()`
      ≥604800s/7-day bar cited in `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a) on all 3 sibling prd
      sports buckets named in `issues/sports_player_stats_empty_write_followups_2026_07_26.md`
      (`instruments-store-sports-prd-central-element-323112`, `features-sports-prd-central-element-323112`,
      `market-data-tick-sports-prd-central-element-323112`) — raised from the 604800s (7-day) baseline that doc's own
      `[OPERATOR] P2` item had already verified fleet-wide (2026-07-27) up to **2,592,000s (30 days)**, comfortably
      above the §3a floor. **No terraform change** — matched the exact precedent of the prior 7-day fix (per that source
      doc: applied imperatively via `gcloud storage buckets update`, not tracked in `canonical_buckets.tf`, which
      declares no `soft_delete_policy` block for any canonical bucket, so there is no terraform-state drift risk
      introduced). **Verified live** (fresh
      `gcloud storage buckets describe --format='value(soft_delete_policy.retentionDurationSeconds)'` run this session,
      all 3 buckets): each reads `2592000`. Source doc
      (`issues/sports_player_stats_empty_write_followups_2026_07_26.md`) is `status: resolved` + archived — left
      untouched per its own note ("its own tag/text still needs syncing... this todo carries the actual ruling... so the
      fix isn't blocked on that sync"); this todo's evidence here is the durable record.

- [ ] [DATA] P3. **RULED 2026-07-28 (applying the operator's adapter/feature-completion theme: "All adaptors should be
      FINISHED with respect to data, UNLESS it is literally proven the data cannot be obtained — in which case the
      adaptor/feature should be FULLY REMOVED... No half-built, half-referenced adaptors left lying around either way,"
      extended here to feature COLUMNS rather than adapters) — retagged away from `[OPERATOR/DESIGN]`, moved out of
      Deferred.** `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md`'s 5 unfilled xG column
      groups (per-source passthroughs, disagreement/range, derived consensus, historical accuracy, league rank) default
      to **BUILD, not prune** — the theme does not accept "uncertain model value" as grounds for removal, only a PROVEN
      data-infeasibility does. For each of the 5 groups: (1) investigate whether the underlying inputs are actually
      obtainable from already-captured per-source data (the doc's own framing suggests most are — e.g. per-source
      passthroughs and disagreement ranges are pure derived computations over odds/xG data this pipeline already
      captures, not a new data source); (2) if feasible, implement the group to FULL completion in
      `MULTISOURCE_XG_COLUMNS` (no partial/placeholder columns); (3) only if a group is proven infeasible (the source
      data genuinely does not exist anywhere reachable), fully remove it — from `MULTISOURCE_XG_COLUMNS`, any UAC schema
      reference, the manifest, and docs, per the "no half-built, half-referenced" mandate — rather than leaving a schema
      column nobody computes. That source doc is outside this batch's file scope; its own `[OPERATOR/DESIGN]` tag still
      needs syncing to this ruling when next touched. Repo: features-service. **Done when**: each of the 5 groups
      carries either a shipped, fully-computed implementation or a proven-infeasible removal (column purged from
      schema/manifest/docs), with no group left half-built or merely diagnosed. **Investigated 2026-07-30 (operator-
      ruling closeout pass) — feasibility is genuinely mixed per group, not implemented this pass.** Read
      `multisource_xg_calculator.py` + `gcs_normalizers.py` directly (not assumed): per-source passthrough for
      `home_xg_understat`/`away_xg_understat` IS mechanically buildable today (the raw normalizer already produces
      exactly those column names — `_normalize_understat_xg`, confirmed real data). But
      `home_xg_footystats`/`away_xg_footystats`/`home_xg_api_football`/`away_xg_api_football` are NOT — grepped the
      whole repo and found these 4 names exist NOWHERE outside this calculator's own dead column declarations;
      FootyStats' raw normalizer (`_normalize_footystats_matches`) produces unsuffixed `home_xg`/`away_xg` columns, not
      per-source-suffixed ones, and no merge step anywhere renames/joins them into `target_fixtures` under the suffixed
      names this calculator expects — so 4 of the 6 per-source-passthrough columns need new upstream data-plumbing (a
      real, not-yet-scoped change to the fixture-assembly/merge step), not just a calculator edit. The other 3 groups
      (disagreement/range, derived-consensus formulas, historical-accuracy, league-rank) all need genuine per-group
      feature-engineering DESIGN decisions with no formula specified anywhere in this corpus (e.g. the exact
      Poisson/heuristic form for `xg_implied_over_2_5`, the historical-accuracy lookback window, the league-rank
      tie-break rule) — inventing these silently risks shipping plausible-but-wrong ML training features, which this
      task's own guardrails (no policy/design calls, data-pipeline-correctness-is-the-heartbeat) weigh against
      improvising alone. Left un-implemented and the checkbox unflipped rather than partially done or guessed; whoever
      picks this up next should start from the `home_xg_understat` passthrough (the one group confirmed mechanically
      ready) and treat the other 4 groups' exact formulas as their own scoped sub-decisions.

- [ ] [DATA] P3. **`issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md`'s ownership-routing todo — ALREADY
      RULED 2026-07-28, do not re-draft here.** Operator direct answer: _"This isn't actually a real open question —
      check the code and just re-run/dispatch it. Convert to a normal task, do not leave as an operator-facing
      question."_ That issue doc (one of this same operator-decisions pass's assigned files) has already been retagged
      from `[OPERATOR]` to `[DATA] P3` with the full task (re-read the adapter, attempt a live re-fetch of the 4 dates
      via the historical endpoint, close as backfilled-or-proven-permanent-absence either way) — execute that doc's own
      Todos section item, not this pointer. Removed from Deferred here since it is no longer an open operator question.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` § Z `[DATA] P3` — matchday recovery:
  regex-from-`round_name` vs the Track F corpus re-run.** § Z's todo says _"recover `matchday` from the persisted
  `round_name` (regex) rather than re-running the whole features corpus"_, and its own § Z framing justifies this as
  cheap ("`round_name` persists at 100%, and `matchday` is a pure regex over it"). Side B: the closeout's **Track F**
  mandates a clean corpus-wide `derived_features` re-run (plus a PURGE of the fabricated post-floor remainder and a
  census re-verify), which would recompute `matchday` anyway. Both are open and live. The conflict is an ORDERING one
  and it is not resolvable from evidence: run the regex pass BEFORE the re-run and the work is discarded; run it AFTER
  and it is redundant; run it DURING and it races the re-run's writes to the same shards. Track F's chain is itself
  gated (the PURGE is explicitly "only after the re-run todo above is done", and the re-run is not scheduled), so "just
  wait for Track F" is not currently a bounded answer either. Recommended resolution for the operator/plan-owner: state
  in the closeout's Track F whether the regex recovery is (a) superseded — delete § Z's todo, or (b) a sanctioned
  interim fix with an explicit "only if Track F's re-run has not started by <date>" gate. No candidate todo drafted.

- **Reconcile-in-place vs archive-as-history for the two features-sweep parts.** Todos 1 and 2 above assume the parts
  stay in `plans/active/issues/` and get reconciled in place. The alternative — archive §§ G-AA wholesale as historical
  record and re-file only the ~4 genuinely-live items as fresh issue docs — is the treatment two sibling docs already
  got (`/plans/archive/2026_07/sports_consolidated_closeout_track_d_history_2026_07_23.md`,
  `sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`, the very precedent the split itself cites). Both
  parts self-describe as _"Record + live-work hybrid, not archive-only"_, which argues for in-place, but a doc where the
  large majority of checkboxes are provably terminal is exactly what the history-extraction pattern exists for. This is
  a plan-lifecycle decision, not an evidence question. Parked; todos 1 and 2 are drafted against the in-place option and
  should be re-scoped if the operator prefers archive-as-history.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` `[CODE] P3`** — wire `--family` to
  actually scope SPORTS training, or drop the required-argument validation. Confirmed still true this audit
  (validated-but-never-consumed: zero hits outside the argparse definition). The doc's own slot-6 annotation defers it
  explicitly: _"this doc's own framing ('either wire it or drop it') is a genuine design decision, not a mechanical
  fix"_. Its sibling `[ML] P2` retrain is NOT deferred here — it is already tracked by batch5's open `[CODE] P1` PARTIAL
  todo, which carries the whole `(c)` chain.

- **Should todo 7's finalize-plan fix be generalised workspace-wide?** Todo 7 is deliberately scoped to the 5 EXISTING
  sports `*_finalize` plans. The same omission exists in every other AG's finalize plans, and the durable fix is to add
  the source-doc-archival step to `plans/active/task_template.md` § 4's finalize-plan-coverage rule (and its codex
  reflection) so future finalize plans are authored with it. That is a change to a workspace-wide AUTHORING RULE
  affecting every AG, which is the operator's call, not a worker's — so it is parked rather than folded into todo 7.
  **Recommended**: approve the generalisation; the sports-only fix leaves 4 other AGs reproducing the same
  CI-gate-escalation loop.

- **Which tranche owns `plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md`? It currently falls
  through every tranche's audit.** Its `asset_group` is bare `[cross-cutting]`, which on filename alone (`sports_`
  prefix) looks like the skill's Phase-0.3 "pattern 3" fork-inherited mistag — but a full content read says the tag is
  CORRECT: the work is a `MANIFEST_SCHEMA_VERSION` 9→10 bump on UTL's `AvailabilityRecord`, the ONE manifest-row
  dataclass every asset_group and every producer service writes, needing a full-fleet redeploy. So it is genuinely
  cross-AG and must NOT be retagged `[sports]`. **But it is invisible to every tranche**: zero sports covering plans
  cite it (verified across all 17), and its `parent_epic: deployment_and_user_management_master` is not in the
  `cross-cutting` tranche's own membership rule (that rule admits only `infrastructure_master`'s data subset,
  `instruments_master`, `mtds_mdps_master`, `manifest_master`, `features_and_ml_master`), so `cross-cutting`'s audit
  will not pick it up either. Its 1 open P2 todo therefore has no owning tranche at all. This is a
  tranche-classification/authority call spanning `cross-cutting`/`ci`/`infra`, outside a sports batch's scope.
  **Recommended**: assign it to the `infra` tranche (which already splits `deployment_and_user_management_master`
  content per the skill's own membership note) and add it to that tranche's consolidated-closeout Sources list.

## Not re-surfaced here (already owned — checked, not assumed)

- **batch5's own 16 Deferred items** (4 conflict-gated + 12 operator-gated). `batch5_finalize` todo 2 owns their
  re-check verbatim and names `batch6` as the extraction destination for any that clear. Drafting them here would
  front-run that gated todo and duplicate its work. Their docs therefore classify orphaned-but-owned, not fresh orphans.
- **`issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s `[ML] P2`** and
  **`issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`'s `[ML] P2`** —
  both are the same retrain, the latter explicitly marked SUPERSEDED and pointing at the former, and both sit inside the
  chain batch5's open `[CODE] P1` PARTIAL todo tracks. Already covered.
- **The `[VERIFY] P2` rebuild-delta reconciliation** — a verbatim duplicate of an existing `native_ao_extract` todo;
  only the missing cross-link was drafted (todo 9).

## Codex SSOTs (read before touching a todo)

`/codex/02-data/sports-2020-06-data-floor.md`, `…/sports-data-types-catalog.md`, `…/sports-gcs-path-ssot.md`,
`…/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`,
`/codex/05-infrastructure/gcs-object-operations.md` (todo 3's `resolve_bucket_name` rule),
`/codex/05-infrastructure/spot-vms-for-backfill.md`, `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule
1a — todo 3's monitoring hazard), `/codex/11-project-management/issue-doc-lifecycle.md` (todo 7). Plan↔codex drift is
review-blocking.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
