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
status: draft
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
    /plans/active/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
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
---

# Sports satellite AO batch 6 — post-batch5 orphans

> **⚠️ `status: draft` — NOT dispatched.** Drafted autonomously per the `/ag-closeout-audit` skill's Autonomous-mode
> rule: drafting a `status: draft` pair is safe unattended, but flipping it to `active` is the operator's call. Do not
> flip without explicit approval. Its gated companion is
> `/plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26_finalize.md` (also `status: draft`).

> **Why a batch6 exists one day after batch5.** `batch5_finalize` todo 2's own text names the destination: _"extract it
> as a new tracked todo in a follow-up `batch6`"_. batch5 is `status: active`, mid-dispatch, and already at its
> 1000-line hard cap — its Deferred items cannot be folded back into it, and the orphans below did not exist when its
> Phase-1 snapshot was taken.

## Cross-todo file-collision check (done before finalizing, per the skill)

Same-priority todos in one plan run concurrently by default, so same-priority todos must touch distinct files.

| priority | todos      | files touched                                                                        | collision |
| -------- | ---------- | ------------------------------------------------------------------------------------ | --------- |
| P1       | 1, 2, 4, 7 | part2 / part3 / capture-outage doc + mtds / the 5 sports `*_finalize` plans          | none      |
| P2       | 3, 8, 9    | `launch-features-vm.sh` + part3 / naming doc + its parent plan / `native_ao_extract` | none      |
| P3       | 5, 6       | `instruments-service/scripts/` / `features_service/sports/`                          | none      |

**One deliberate ordering dependency, handled by priority rather than `sequential: true`** (which would needlessly
serialise all 9): todo 3 (P2) flips a checkbox inside part3, which todo 2 (P1) also edits. P1 drains before P2, so todo
2 lands first. Todo 2's text is explicit that it must LEAVE the § Y checkbox open and annotate it as owned by todo 3.

## Todos

- [ ] [DOC] P1. **Reconcile `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`'s 24 open checkboxes
      against their real current state — and neutralise the reversed-casing hazard in its § K block FIRST.** This doc
      was created 2026-07-26 by batch5's own § A2 line-cap split of the 1,843-line parent; every covering-plan citation
      still names the PRE-split filename, so §§ G-N's 24 open todos are structurally uncovered. **Safety-critical
      sub-part, do this before anything else in this todo**: § K1/§ K2 still carry open todos reading _"DIRECTION
      CORRECTED — emit UPPER, not lower"_ and _"QG assertion: sports `data_type` ∈ the UAC **UPPER-case** sports
      vocabulary (per K0-DECISION (b))"_, citing the operator's 2026-07-18 K0-DECISION. That decision was **REVERSED
      2026-07-23** — `sports_consolidated_closeout_2026_07_19.md`'s Canonical-target section states _"data_type =
      LOWER-case everywhere for sports — FINAL, reconciled 2026-07-23"_ and _"This REVERTS Track C's K1/K2 work below"_.
      A worker picking up part2 § K1 today ships the WRONG casing direction — **this exact failure has already happened
      once**, recorded in
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
      `issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`.

- [ ] [DOC] P1. **Reconcile `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`'s 31 open checkboxes
      against their real current state.** Same split origin and same structural orphaning as todo 1, for §§ O-AA. This
      part is the higher-yield half because the doc contains its own terminal-state evidence: the **"Round work —
      TERMINAL STATE (2026-07-19)"** table records § Q's derivation (115,715 rows, ZERO api-football calls), § T's
      194-pair backfill (10,438 rows, 191/194 pairs cleared) and § W's 159-pair backfill (16,435 rows, 158/159) as all
      complete and corpus-re-scan-verified, and then states _"Every remaining in-window blank is accounted for — nothing
      is unexplained"_ with a reconciling 11,276-row table — yet the § Q/§ T/§ W `[ ]` todos that the table closes are
      still unchecked. Flip those against that table. Then route the rest by owner rather than re-deriving: § R's
      ~9-stale-entity-consumer audit is owned by the closeout's **Track E** (which cites _"sweep § R's ~9-file list, now
      7"_ verbatim); § S/§ X/§ Z-FIXED's features re-run items are owned by the closeout's **Track F** (§ Z-FIXED's own
      todo already says _"Tracked in `sports_consolidated_closeout_2026_07_19.md` FEATURES track"_); § O's catalogue
      rebuild is owned by Track V's `build_instrument_catalogue.py --asset-group sports --since     2019-01-01` re-roll;
      § T's pre-2019 `[DECISION]` and § U's 489-non-registry-pair `[DECISION]` were both **ANSWERED 2026-07-20** by
      Track V's § T and § U operator decisions (out-of-scope / excluded-from-denominator respectively) — flip both
      citing those. **Leave § Y's `[CODE] P2` launcher-hint todo OPEN and annotate it `owned by batch6 todo 3`** — todo
      3 ships that fix and flips it; do not flip it here or you will race todo 3's evidence line. **Leave § Z's
      `[DATA] P3` matchday-regex-recovery todo OPEN and annotate it as parked** — see this plan's Deferred section, it
      is a genuine mechanism conflict with Track F's re-run, not a stale checkbox. Repo: unified-trading-pm. **Done
      when**: all 31 checkboxes carry an `[x]` with cited evidence, an owner annotation, or a stated reason they remain
      open; § Y and § Z carry the two named annotations; `check_line_caps.sh` still passes on the file. Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`.

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
      (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`). Repo: deployment-service. **No `[OPERATOR]` gate
      needed (`task_template.md` finding O justification)**: this todo names a VM launcher (`launch-features-vm.sh`) and
      so trips the `check_delete_vm_launch_gating.sh` soft pre-filter, but it **launches no VM, writes no GCS object and
      deletes nothing** — the entire change is to the launcher's printed post-backfill HINT TEXT (a Python bucket-name
      string it echoes for the operator to copy), shipped as source via the normal quickmerge path, and its done-when is
      a `quality-gates.sh` run plus a checkbox flip. Safe-idempotent by construction. **Coordination**: todo 2 (P1,
      drains first) leaves part3's § Y checkbox open and annotated for you — flip it as part of THIS todo's evidence,
      and do not make any other edit to part3. **Done when**: the hint resolves both the bucket and the prefix through
      `resolve_bucket_name`/the real `sports_features/` prefix, a `quality-gates.sh` run is green on deployment-service,
      and part3's § Y checkbox is `[x]` with the shipping sha. Source:
      `issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` § Y.

- [ ] [DATA] P1. **`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` carries `assigned_vm: planning`
      but ZERO checkboxes — convert its 3 prose next-steps into tracked todos, then execute the 2 bounded ones.** This
      doc is marked for orchestrator dispatch (`assigned_vm: planning`, `execution_scope: orchestrator-agent`) yet
      `regen_backlog_from_plan.py` derives todos from checkboxes, so its work is structurally invisible to the backlog —
      it can never be dispatched in its current shape. Step 1: convert the three items under "Recommended decision /
      next steps" into properly-tagged `- [ ]` checkboxes under a `## Todos` heading, preserving their text verbatim.
      Step 2: leave item 1 (the ~1-month-gap backfill decision) as an `[OPERATOR] P0` checkbox — it is a
      credits/priority call, explicitly not a worker one; note in it that the DEPLOY half of that item is already
      satisfied by the doc's own dated correction banner (_"DEPLOY CONFIRMED (2026-07-26, directly verified, not
      inferred)"_, image `f6001`/`410d756` digests + a log-inspected post-deploy execution with zero
      `DATA_NOT_AVAILABLE`), so only the backfill fork remains. Step 3: execute item 2 — verify whether DeFi's same-day
      capture was also blocked by the same `TickDataHandler._check_early_exit` future-date guard (the removed design
      comment said _"DeFi: immediate"_ too, and the fix `market-tick-data-service@410d7569` put DEFI on the relaxed
      branch, so the question is whether historical DeFi capture was starved before it landed). **Check the defi
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

- [ ] [SCRIPT] P3. **Audit `instruments-service/scripts/` for the missing "refuse to write an empty/0-row result" guard
      that caused the player_stats empty-write incident.** Any script that builds a `pd.DataFrame(records)` from a
      possibly-empty `records` list and writes it without checking for an empty result is a candidate. The incident this
      generalises from (`/plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md`)
      briefly wrote 240 objects empty on a first `--apply`; it was recoverable ONLY because the source was a
      re-fetchable external API — the same bug against internally-derived canonical data would be permanent loss under
      the affected bucket's current zero-retention policy. Add the guard wherever missing. Repo: instruments-service.
      **Done when**: every matching script either has the guard or is confirmed not to need it, with a one-line note per
      script, and `quality-gates.sh` is green. Source: `issues/sports_player_stats_empty_write_followups_2026_07_26.md`
      (`[SCRIPT]` item). **Note**: that doc's sibling `[OPERATOR] P2` item (enabling GCS object versioning / soft-delete
      retention on the sports prd buckets) is deliberately NOT extracted here — it is an infra spend decision, see the
      Deferred section.

- [ ] [REVIEW] P3. **Sweep `features_service/sports/` for the same `= pd.NA`-then-never-filled idiom that upcast 23 xG
      columns to object dtype and crashed the first real SPORTS model fit.** The root cause is already fixed at one site
      (`features-service@c54f9eaf`: `multisource_xg_calculator.py`'s `out[col] = pd.NA` → `np.nan`, since `pd.NA`
      upcasts a column to `object`, which then survives GCS write/read and poisons ml-service's cross-date merge). The
      open question is whether the idiom exists elsewhere. **One named lead to check first, not just a blind grep**: the
      investigation that found the original flagged `writer.py`'s `season_context` columns as using an identical
      "initialized to `pd.NA`" pattern per its own code comment — that was never independently verified as dead, only
      flagged. Repo: features-service. **Done when**: every `pd.NA` initialisation site under `features_service/sports/`
      is listed with a verdict (genuinely filled later / never filled → converted to `np.nan` / not a dtype risk),
      `writer.py`'s `season_context` case is explicitly resolved either way, and `quality-gates.sh` is green. Source:
      `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md` (`[REVIEW]` item). **Note**: that
      doc's sibling `[OPERATOR/DESIGN] P3` item (decide which of the 5 unfilled xG column groups to build vs prune) is
      deliberately NOT extracted — the doc itself stops at diagnosis per the dispatch-scope rule.

- [ ] [DOC] P1. **Add the missing source-doc-archival todo to the 5 sports `*_finalize` plans — the omission is why a CI
      gate had to auto-remediate 11 docs at 02:57Z today.** `task_template.md` § 4's finalize-plan rule has three parts:
      reconcile source-doc checkboxes, re-check deferred items, archive **the plan**. Nothing archives the SOURCE docs
      the batch drove to terminal status. Concretely, `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md` todo
      1 says _"Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos"_ — flipping a doc to
      `resolved` while it sits in `plans/active/issues/` is exactly what `check_terminal_status_archived.py` HARD-fails
      on. So the finalize plan, as written, creates the hygiene violation, and today the `plan_health` gate's own
      remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545) archived all 11 rather than any
      plan owning it. Add a 4th todo to each of the 5 sports finalize plans —
      `sports_satellite_ao_dispatch_batch{2,3,4,5}_*finalize*.md` and
      `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` — reading, in substance: _"Archive every source doc
      this batch drove to `status: resolved`/`complete` (verify 0 open todos + a genuine resolution banner on each
      first), in the same commit as the flip, so `check_terminal_status_archived.py` never sees a terminal doc in
      `plans/active/`."_ Repo: unified-trading-pm. **Done when**: all 5 finalize plans carry the new todo, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures. Source:
      `issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2 (the "one durable gap this leaves" note —
      filed there explicitly as _"a small authoring change, not a decision"_). **Scope guard**: do NOT edit
      `plans/active/task_template.md` § 4 or the codex rule to make this workspace-wide — generalising the authoring
      rule to every AG's finalize plans is parked for the operator (see Deferred).

- [ ] [DOC] P2. **Close out `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` — 2 of its 3
      prose steps are now satisfied by shipped commits.** This doc has zero checkboxes and expresses its remaining work
      as a 3-item prose "Recommended next step" list (the confirmed prose-only trap). Step 1 (flip
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
      plan-destination HARD RULE. If NOT confirmed, stop and record what you measured rather than flipping anything.
      Repo: unified-trading-pm. **Done when**: the doc carries a `## Todos` section with steps 1-2 `[x]` (or an explicit
      measured statement that `0ded2449` is not merged) and step 3 as an unchecked `[OPERATOR]` item, and the parent
      plan's todo 4 matches whatever was actually measured.

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

- **`issues/sports_player_stats_empty_write_followups_2026_07_26.md` `[OPERATOR] P2`** — enable GCS object versioning or
  a bucket-level soft-delete retention window on `instruments-store-sports-prd-central-element-323112` and its sibling
  prd sports buckets. The doc states the ask plainly as needing _"an infra/operator decision on cost vs. blast-radius
  reduction"_. A retention policy change on prod buckets is a recurring-spend commitment, not a worker-determinable
  outcome. Once ruled, the terraform change is a clean bounded todo.

- **`issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md` `[OPERATOR/DESIGN] P3`** — decide, per
  the 5 unfilled xG column groups (per-source passthroughs, disagreement/range, derived consensus, historical accuracy,
  league rank), which are still wanted vs should be pruned from `MULTISOURCE_XG_COLUMNS`. The doc explicitly stops at
  diagnosis and says so: _"'how should `xg_implied_over_2_5` actually be computed' is a design/domain decision, not
  something to improvise without validation"_. This is the textbook "figure out how X should look" pattern the
  dispatch-scope rule excludes. Once each group is ruled keep-or-prune, each kept group becomes a normal scoped todo.

- **`issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md` `[OPERATOR] P3`** — route the 4-consecutive-day
  (2026-06-21..24) meta-only raw-ingestion gap to whoever owns the upstream `venue=ODDS_API` raw writer. The todo's
  action IS the routing, and the destination is a human/ownership call. Note the downstream coupling for whoever rules:
  `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s P2 shard4 retry stays time-gated on this
  resolving upstream — retrying the reprocess cannot produce real bucketed odds for 4 dates that have no real raw odds.

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
